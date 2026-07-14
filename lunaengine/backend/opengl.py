"""
lunaengine/backend/opengl.py

OpenGL-based hardware-accelerated renderer for LunaEngine
- GPU-accelerated particles via instancing (CPU physics)
- Full filter system (post-processing)
- 2D drawing primitives (lines, circles, polygons, etc.)
- Rounded rectangles with per-corner radii
- Texture and surface rendering

This version uses the reliable CPU particle system and only uses OpenGL
for rendering - no compute shaders, no GPU physics.
"""

from __future__ import annotations
import datetime

import pygame
import ctypes
import math
import os
import sys
import time
from typing import Tuple, Dict, Any, List, Optional, Union, Callable
from enum import Enum
import numpy as np
import weakref

from ..utils import math_utils as math_utils
from .types import Color
from ..ui.themes import ThemeStyle

# Check if OpenGL is available
try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("OpenGL not available - falling back to software rendering")

__file_path__ = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# Filter Enums and Classes
# ============================================================================

class FilterType(Enum):
    """Enumeration of all available post-processing filter types."""
    NONE = "none"
    VIGNETTE = "vignette"
    BLUR = "blur"
    SEPIA = "sepia"
    GRAYSCALE = "grayscale"
    INVERT = "invert"
    TEMPERATURE_WARM = "temperature_warm"
    TEMPERATURE_COLD = "temperature_cold"
    NIGHT_VISION = "night_vision"
    CRT = "crt"
    PIXELATE = "pixelate"
    BLOOM = "bloom"
    EDGE_DETECT = "edge_detect"
    EMBOSS = "emboss"
    SHARPEN = "sharpen"
    POSTERIZE = "posterize"
    NEON = "neon"
    RADIAL_BLUR = "radial_blur"
    FISHEYE = "fisheye"
    TWIRL = "twirl"


class FilterRegionType(Enum):
    """Defines the shape/region where a filter is applied."""
    FULLSCREEN = "fullscreen"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"


class Filter:
    """
    Represents a post-processing filter with configurable region and intensity.

    Attributes:
        filter_type (FilterType): The type of effect to apply.
        intensity (float): Strength of the effect (0.0 to 1.0).
        region_type (FilterRegionType): Shape of the affected area.
        region_pos (Tuple[float, float]): Position (top‑left for rect, center for circle).
        region_size (Tuple[float, float]): Width and height of rectangular region.
        radius (float): Radius for circular regions.
        feather (float): Edge softness in pixels.
        blend_mode (str): How the filter blends with the background (e.g., "normal").
        enabled (bool): Whether this filter is active.
        time (float): Accumulated time for animated filters.
    """

    def __init__(self,
                 filter_type: FilterType = FilterType.NONE,
                 intensity: float = 1.0,
                 region_type: FilterRegionType = FilterRegionType.FULLSCREEN,
                 region_pos: Tuple[float, float] = (0, 0),
                 region_size: Tuple[float, float] = (100, 100),
                 radius: float = 50.0,
                 feather: float = 10.0,
                 blend_mode: str = "normal"):
        """
        Initialize a filter with all parameters.

        Args:
            filter_type: Type of filter effect.
            intensity: Filter strength (0.0 to 1.0).
            region_type: Shape of filter region.
            region_pos: Position of region (top-left for rect, center for circle).
            region_size: Size of region (width, height).
            radius: Radius for circular regions.
            feather: Edge softness in pixels.
            blend_mode: How filter blends with background.
        """
        self.filter_type = filter_type
        self.intensity = max(0.0, min(1.0, intensity))
        self.region_type = region_type
        self.region_pos = region_pos
        self.region_size = region_size
        self.radius = max(1.0, radius)
        self.feather = max(0.0, feather)
        self.blend_mode = blend_mode
        self.enabled = True
        self.time = 0.0  # For animated filters

    def update(self, dt: float) -> None:
        """Update filter for animation (e.g., time‑based effects)."""
        self.time += dt

    def copy(self) -> Filter:
        """Create a deep copy of this filter."""
        return Filter(
            self.filter_type,
            self.intensity,
            self.region_type,
            self.region_pos,
            self.region_size,
            self.radius,
            self.feather,
            self.blend_mode
        )


# ============================================================================
# Base Shader Program with Uniform Caching
# ============================================================================

class ShaderProgram:
    """
    Base class for all shader programs with automatic uniform location caching.

    Attributes:
        vertex_source (str | None): Path or source code for vertex shader.
        fragment_source (str | None): Path or source code for fragment shader.
        geometry_source (str | None): Path or source code for geometry shader.
        program (int | None): OpenGL shader program handle.
        vao (int | None): Vertex Array Object handle.
        vbo (int | None): Vertex Buffer Object handle.
        ebo (int | None): Element Buffer Object handle.
    """

    vertex_source: str | None = None
    fragment_source: str | None = None
    geometry_source: str | None = None

    def get_source(self, source: str | None, type: str) -> None:
        """
        Load shader source from a file if the provided string is a file name.

        Args:
            source: File name or raw source code.
            type: Type of shader ('vertex', 'fragment', 'geometry').
        """
        shaders_folder = os.path.join(os.path.dirname(__file__), '..', 'graphics', 'shaders')
        if source and os.path.exists(shaders_folder):
            if os.path.exists(os.path.join(shaders_folder, source)):
                with open(os.path.join(shaders_folder, source), 'r') as f:
                    content = f.read()
                if type == 'vertex':
                    self.vertex_source = content
                elif type == 'fragment':
                    self.fragment_source = content
                elif type == 'geometry':
                    self.geometry_source = content

    def __init__(self, vertex_source: str, fragment_source: str, geometry_source: Optional[str] = None):
        """
        Initialize the shader program by loading sources and compiling.

        Args:
            vertex_source: File name or raw source for vertex shader.
            fragment_source: File name or raw source for fragment shader.
            geometry_source: Optional file name or raw source for geometry shader.
        """
        self.get_source(vertex_source, 'vertex')
        self.get_source(fragment_source, 'fragment')
        self.get_source(geometry_source, 'geometry')
        self.program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self._uniform_locations: Dict[str, int] = {}
        self._create_program(self.vertex_source, self.fragment_source, self.geometry_source)
        if self.program:
            self._setup_geometry()

    def _get_uniform_location(self, name: str) -> int:
        """Get cached uniform location (avoids repeated glGetUniformLocation calls)."""
        if name not in self._uniform_locations:
            self._uniform_locations[name] = glGetUniformLocation(self.program, name)
        return self._uniform_locations[name]

    def _create_program(self, vertex_source: str, fragment_source: str, geometry_source: Optional[str] = None) -> None:
        """Compile vertex/fragment (and optional geometry) shaders and link the program."""
        try:
            vertex = compileShader(vertex_source, GL_VERTEX_SHADER)
            fragment = compileShader(fragment_source, GL_FRAGMENT_SHADER)
            shaders = [vertex, fragment]
            if geometry_source:
                geometry = compileShader(geometry_source, GL_GEOMETRY_SHADER)
                shaders.append(geometry)
            self.program = compileProgram(*shaders)
        except Exception as e:
            print(f"Shader compilation failed: {e}")
            self.program = None

    def use(self) -> None:
        """Activate this shader program for rendering."""
        if self.program:
            glUseProgram(self.program)

    def unuse(self) -> None:
        """Deactivate the currently active shader program."""
        glUseProgram(0)

    def _setup_geometry(self) -> None:
        """Set up vertex arrays, VBOs, etc. Overridden by subclasses."""
        pass


# ============================================================================
# Particle Shader (Instanced)
# ============================================================================

class ParticleShader(ShaderProgram):
    """Instanced particle rendering shader. Each particle is a point with size and colour."""

    def __init__(self):
        """Initialise the particle shader from external vertex/fragment files."""
        super().__init__(vertex_source='particle.vert', fragment_source='particle.frag')

    def _setup_geometry(self) -> None:
        """
        Set up a dummy VAO with a single vertex (used for instancing).
        Also creates VBOs for instance data (position, size, alpha) and instance colours.
        """
        # One dummy vertex (position doesn't matter)
        vertices = np.array([0.0, 0.0], dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)                     # dummy vertex buffer
        self.instance_data_vbo = glGenBuffers(1)       # x, y, size, alpha per instance
        self.instance_color_vbo = glGenBuffers(1)      # colour per instance

        glBindVertexArray(self.vao)

        # Dummy vertex (location 0)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Instance data (location 1)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_data_vbo)
        glBufferData(GL_ARRAY_BUFFER, 1024 * 4 * 4, None, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribDivisor(1, 1)   # one per instance

        # Instance colour (location 2)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, 1024 * 4 * 4, None, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(2)
        glVertexAttribDivisor(2, 1)   # one per instance

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)


# ============================================================================
# Simple Shader (solid color)
# ============================================================================

class SimpleShader(ShaderProgram):
    """Simple shader for drawing solid colour rectangles and shapes."""

    def __init__(self):
        """Initialise the simple shader from external files."""
        super().__init__(vertex_source='simple.vert', fragment_source='simple.frag')

    def _setup_geometry(self) -> None:
        """Set up a unit quad (0,0) to (1,1) with index buffer."""
        vertices = np.array([
            0.0, 0.0,
            1.0, 0.0,
            1.0, 1.0,
            0.0, 1.0
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindVertexArray(0)


# ============================================================================
# Texture Shader
# ============================================================================

class TextureShader(ShaderProgram):
    """Shader for rendering textured quads (surfaces, images)."""

    def __init__(self):
        """Initialise the texture shader from external files."""
        super().__init__(vertex_source='texture.vert', fragment_source='texture.frag')

    def _setup_geometry(self) -> None:
        """Set up a quad with position and UV coordinates."""
        vertices = np.array([
            # pos        # tex
            0.0, 0.0,    0.0, 0.0,
            1.0, 0.0,    1.0, 0.0,
            1.0, 1.0,    1.0, 1.0,
            0.0, 1.0,    0.0, 1.0
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize,
                              ctypes.c_void_p(2 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)


# ============================================================================
# Rounded Rectangle Shader
# ============================================================================

class RoundedRectShader(ShaderProgram):
    """Shader that draws rectangles with per‑corner rounded corners using signed distance fields."""

    def __init__(self):
        """Initialise the rounded rectangle shader from external files."""
        super().__init__(vertex_source='rounded_rect.vert', fragment_source='rounded_rect.frag')

    def _setup_geometry(self) -> None:
        """Set up a simple quad geometry (the shader handles rounding)."""
        vertices = np.array([
            0.0, 0.0,
            1.0, 0.0,
            1.0, 1.0,
            0.0, 1.0
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindVertexArray(0)


# ============================================================================
# Filter Shader (post-processing)
# ============================================================================

class FilterShader(ShaderProgram):
    """Full‑screen quad shader for applying post‑processing filters and effects."""

    def __init__(self):
        """Initialise the filter shader from external files."""
        super().__init__(vertex_source='filter.vert', fragment_source='filter.frag')

    def _setup_geometry(self) -> None:
        """Set up a full‑screen quad (clip space coordinates)."""
        vertices = np.array([
            -1.0,  1.0,  0.0, 1.0,
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0,
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)

        glBindVertexArray(self.vao)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize,
                              ctypes.c_void_p(2 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)


# ============================================================================
# Main OpenGLRenderer
# ============================================================================

class OpenGLRenderer:
    """
    Main hardware‑accelerated renderer for LunaEngine.

    Manages OpenGL context, shaders, framebuffers, geometry caches,
    filters, particles, and all drawing operations.

    Attributes:
        width (int): Current viewport width.
        height (int): Current viewport height.
        camera_position (pygame.math.Vector2): World camera position.
        filters (List[Filter]): Active post‑processing filters.
    """

    camera_position = pygame.math.Vector2(0, 0)

    def __init__(self, width: int, height: int):
        """
        Initialise the OpenGL renderer with given screen dimensions.

        Args:
            width: Initial viewport width.
            height: Initial viewport height.
        """
        self.width = width
        self.height = height
        self._initialized = False

        # Shader instances
        self.simple_shader: SimpleShader | None = None
        self.texture_shader: TextureShader | None = None
        self.particle_shader: ParticleShader | None = None
        self.filter_shader: FilterShader | None = None
        self.rounded_rect_shader: RoundedRectShader | None = None

        # Particle system integration
        self._max_particles = 1024
        self.on_max_particles_change: List[Callable[[int], None]] = []

        # Filter system
        self.filters: List[Filter] = []
        self._filter_framebuffer = None
        self._filter_texture = None
        self._filter_renderbuffer = None

        # Geometry caches
        self._circle_cache: Dict[Any, Tuple[int, int, int, int]] = {}
        self._polygon_cache: Dict[Any, Tuple[int, int, int, int]] = {}

        # Current render target
        self._current_target: pygame.Surface | None = None

        # ---- FIXED TEXTURE CACHE ----
        # Now uses WeakKeyDictionary to avoid ID reuse issues.
        # Outer: surface -> inner dict (sub_key -> (tex, size, last_use))
        # Sub_key = (rect_tuple, dest_tuple, flags)
        self._texture_cache = weakref.WeakKeyDictionary()

        # Text cache
        self._text_cache: Dict[Tuple[str, pygame.font.Font, Tuple[int, int, int], Tuple[bool, bool]], Tuple[int, Tuple[int, int]]] = {}
        self._text_cache_last_used: Dict[Tuple[str, pygame.font.Font, Tuple[int, int, int], Tuple[bool, bool]], float] = {}
        self._text_cache_timeout: float = 10.0
        self._texture_cache_timeout: float = 10.0
        self._last_texture_cache_cleanup: float = 0.0
        self._last_text_cache_cleanup: float = 0.0
        self._text_cache_cleanup_interval: float = 5.0
        
        self._scissor_stack: List[Tuple[int, int, int, int]] = []
        
    def get_opengl_version(self) -> str:
        return glGetString(GL_VERSION).decode('ascii')

    def set_text_cache_timeout(self, seconds: float) -> None:
        """
        Set how long a text texture stays in cache without being used.

        Args:
            seconds: Timeout in seconds (>= 0.1).
        """
        self._text_cache_timeout = max(0.1, seconds)

    def get_cache_usage(self, target: str = 'all', humanize: bool = False) -> float | Dict[str, float]:
        """
        Return cache usage as size in bytes or as a dictionary of sizes.

        Args:
            target: One of 'text', 'texture', 'circle', 'polygon', 'total', or 'all'.
            humanize: If True, return human‑readable strings (e.g., "1.2 KB").

        Returns:
            Size in bytes (or humanised string) or a dictionary of all caches.
        """
        if target == 'all':
            return {
                'text': math_utils.humanize_size(sys.getsizeof(self._text_cache)) if humanize else sys.getsizeof(self._text_cache),
                'texture': math_utils.humanize_size(sys.getsizeof(self._texture_cache)) if humanize else sys.getsizeof(self._texture_cache),
                'circle': math_utils.humanize_size(sys.getsizeof(self._circle_cache)) if humanize else sys.getsizeof(self._circle_cache),
                'polygon': math_utils.humanize_size(sys.getsizeof(self._polygon_cache)) if humanize else sys.getsizeof(self._polygon_cache),
                'total': self.get_cache_usage('total', humanize)
            }
        elif target == 'text':
            val = sys.getsizeof(self._text_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == 'texture':
            val = sys.getsizeof(self._texture_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == 'circle':
            val = sys.getsizeof(self._circle_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == 'polygon':
            val = sys.getsizeof(self._polygon_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == 'total':
            total = (sys.getsizeof(self._text_cache) + sys.getsizeof(self._texture_cache) +
                     sys.getsizeof(self._circle_cache) + sys.getsizeof(self._polygon_cache))
            return math_utils.humanize_size(total) if humanize else total
        else:
            raise ValueError(f"Invalid cache target: {target}")

    @property
    def max_particles(self) -> int:
        """Maximum number of particles that can be rendered simultaneously."""
        return self._max_particles

    @max_particles.setter
    def max_particles(self, value: int) -> None:
        """
        Change the maximum particle count and trigger resize callbacks.

        Args:
            value: New maximum number of particles.
        """
        if value > self._max_particles:
            for callback in self.on_max_particles_change:
                callback(value)
        self._max_particles = value

    def initialize(self) -> bool:
        """
        Set up OpenGL context, compile shaders, create framebuffers.

        Returns:
            True if initialisation succeeded, False otherwise.
        """
        if not OPENGL_AVAILABLE:
            return False

        print(f"Initializing OpenGL renderer for {self.width}x{self.height}...")

        # Set up OpenGL state
        glDisable(GL_FRAMEBUFFER_SRGB)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.3, 1.0)
        glEnable(GL_PROGRAM_POINT_SIZE)

        # Create shaders
        self.simple_shader = SimpleShader()
        self.texture_shader = TextureShader()
        self.particle_shader = ParticleShader()
        self.filter_shader = FilterShader()
        self.rounded_rect_shader = RoundedRectShader()

        if not all([self.simple_shader.program, self.texture_shader.program,
                    self.particle_shader.program, self.filter_shader.program,
                    self.rounded_rect_shader.program]):
            print("Shader initialization failed")
            return False

        # Initialise filter framebuffer
        self._initialize_filter_framebuffer()

        self._initialized = True
        print("OpenGL renderer initialized successfully")
        return True

    def _initialize_filter_framebuffer(self) -> bool:
        """
        Create the off‑screen framebuffer used for applying filters.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self._filter_framebuffer = glGenFramebuffers(1)
            self._filter_texture = glGenTextures(1)
            self._filter_renderbuffer = glGenRenderbuffers(1)

            glBindTexture(GL_TEXTURE_2D, self._filter_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height,
                         0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            glBindRenderbuffer(GL_RENDERBUFFER, self._filter_renderbuffer)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)

            glBindFramebuffer(GL_FRAMEBUFFER, self._filter_framebuffer)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._filter_texture, 0)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT,
                                      GL_RENDERBUFFER, self._filter_renderbuffer)

            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                print("Filter framebuffer is not complete!")
                return False

            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            return True
        except Exception as e:
            print(f"Failed to initialize filter framebuffer: {e}")
            return False

    # ========================================================================
    # Filter System Methods
    # ========================================================================

    def add_filter(self, filter_obj: Filter) -> None:
        """Add a filter to the active filter stack."""
        self.filters.append(filter_obj)

    def remove_filter(self, filter_obj: Filter) -> None:
        """Remove a specific filter from the stack."""
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)

    def clear_filters(self) -> None:
        """Remove all active filters."""
        self.filters.clear()

    def create_quick_filter(self, filter_type: FilterType, intensity: float = 1.0,
                            x: float = 0, y: float = 0,
                            width: float = None, height: float = None,
                            radius: float = 50.0, feather: float = 10.0) -> Filter:
        """
        Create and add a filter with common sensible defaults.

        Args:
            filter_type: Type of filter effect.
            intensity: Strength (0.0 to 1.0).
            x, y: Position of the region.
            width, height: Dimensions of rectangular region (if None, uses screen size).
            radius: Circle radius (if circular region).
            feather: Edge softness.

        Returns:
            The created Filter object (already added to the stack).
        """
        if width is None or height is None:
            width, height = self.width, self.height

        region_type = FilterRegionType.FULLSCREEN
        if width < self.width or height < self.height:
            region_type = FilterRegionType.RECTANGLE
        if filter_type in [FilterType.VIGNETTE, FilterType.CRT]:
            region_type = FilterRegionType.FULLSCREEN

        filter_obj = Filter(
            filter_type=filter_type,
            intensity=intensity,
            region_type=region_type,
            region_pos=(x, y),
            region_size=(width, height),
            radius=radius,
            feather=feather
        )
        self.add_filter(filter_obj)
        return filter_obj

    # Quick filter helpers
    def apply_vignette(self, intensity: float = 0.7, feather: float = 100.0) -> Filter:
        """Add a vignette (darkened edges) effect."""
        return self.create_quick_filter(FilterType.VIGNETTE, intensity, feather=feather)

    def apply_blur(self, intensity: float = 0.5, x: float = 0, y: float = 0,
                   width: float = None, height: float = None) -> Filter:
        """Add a gaussian‑like blur effect, optionally within a rectangle."""
        return self.create_quick_filter(FilterType.BLUR, intensity, x, y, width, height, feather=20.0)

    def apply_sepia(self, intensity: float = 1.0) -> Filter:
        """Add a sepia tone (warm brownish) effect."""
        return self.create_quick_filter(FilterType.SEPIA, intensity)

    def apply_grayscale(self, intensity: float = 1.0) -> Filter:
        """Convert colours to grayscale."""
        return self.create_quick_filter(FilterType.GRAYSCALE, intensity)

    def apply_invert(self, intensity: float = 1.0) -> Filter:
        """Invert colours (negative)."""
        return self.create_quick_filter(FilterType.INVERT, intensity)

    def apply_warm_temperature(self, intensity: float = 0.5) -> Filter:
        """Increase warm colours (orange/red)."""
        return self.create_quick_filter(FilterType.TEMPERATURE_WARM, intensity)

    def apply_cold_temperature(self, intensity: float = 0.5) -> Filter:
        """Increase cold colours (blue)."""
        return self.create_quick_filter(FilterType.TEMPERATURE_COLD, intensity)

    def apply_night_vision(self, intensity: float = 0.9) -> Filter:
        """Simulate night vision (green tint + noise)."""
        return self.create_quick_filter(FilterType.NIGHT_VISION, intensity)

    def apply_crt_effect(self, intensity: float = 0.8) -> Filter:
        """Add CRT monitor scanlines and curvature."""
        return self.create_quick_filter(FilterType.CRT, intensity)

    def apply_pixelate(self, intensity: float = 0.7) -> Filter:
        """Pixelate the image (lower resolution)."""
        return self.create_quick_filter(FilterType.PIXELATE, intensity)

    def apply_bloom(self, intensity: float = 0.5) -> Filter:
        """Add a bloom (glow) effect around bright areas."""
        return self.create_quick_filter(FilterType.BLOOM, intensity)

    def apply_edge_detect(self, intensity: float = 0.8) -> Filter:
        """Detect and highlight edges."""
        return self.create_quick_filter(FilterType.EDGE_DETECT, intensity)

    def apply_emboss(self, intensity: float = 0.7) -> Filter:
        """Apply an emboss (raised edges) effect."""
        return self.create_quick_filter(FilterType.EMBOSS, intensity)

    def apply_sharpen(self, intensity: float = 0.5) -> Filter:
        """Sharpen the image."""
        return self.create_quick_filter(FilterType.SHARPEN, intensity)

    def apply_posterize(self, intensity: float = 0.6) -> Filter:
        """Reduce the number of colour bands."""
        return self.create_quick_filter(FilterType.POSTERIZE, intensity)

    def apply_neon(self, intensity: float = 0.7) -> Filter:
        """Add a neon glow effect."""
        return self.create_quick_filter(FilterType.NEON, intensity)

    def apply_radial_blur(self, intensity: float = 0.5) -> Filter:
        """Blur outward from the centre."""
        return self.create_quick_filter(FilterType.RADIAL_BLUR, intensity)

    def apply_fisheye(self, intensity: float = 0.4) -> Filter:
        """Apply a fisheye lens distortion."""
        return self.create_quick_filter(FilterType.FISHEYE, intensity)

    def apply_twirl(self, intensity: float = 0.3) -> Filter:
        """Twirl (swirl) the image around its centre."""
        return self.create_quick_filter(FilterType.TWIRL, intensity)

    def apply_circular_grayscale(self, center_x: float, center_y: float,
                                 radius: float = 100.0, intensity: float = 1.0) -> Filter:
        """
        Apply grayscale inside a circular region.

        Args:
            center_x, center_y: Centre of the circle.
            radius: Radius of the circle.
            intensity: Effect strength.
        """
        diameter = radius * 2
        filter_obj = Filter(
            filter_type=FilterType.GRAYSCALE,
            intensity=intensity,
            region_type=FilterRegionType.CIRCLE,
            region_pos=(center_x - radius, center_y - radius),
            region_size=(diameter, diameter),
            radius=1.0,
            feather=20.0
        )
        self.add_filter(filter_obj)
        return filter_obj

    def apply_rectangular_blur(self, x: float, y: float, width: float, height: float,
                               intensity: float = 0.5) -> Filter:
        """
        Apply blur only inside a rectangular region.

        Args:
            x, y: Top‑left corner of the rectangle.
            width, height: Size of the rectangle.
            intensity: Blur strength.
        """
        filter_obj = Filter(
            filter_type=FilterType.BLUR,
            intensity=intensity,
            region_type=FilterRegionType.RECTANGLE,
            region_pos=(x, y),
            region_size=(width, height),
            radius=1.0,
            feather=15.0
        )
        self.add_filter(filter_obj)
        return filter_obj

    # ========================================================================
    # Frame Control
    # ========================================================================

    def begin_frame(self) -> None:
        """
        Start rendering a new frame.

        Binds the filter framebuffer if filters are active and clears the buffer.
        """
        if not self._initialized:
            return
        if self.filters:
            glBindFramebuffer(GL_FRAMEBUFFER, self._filter_framebuffer)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def end_frame(self) -> None:
        """
        Finish rendering the frame and apply any active filters.

        If filters are present, they are applied before swapping buffers.
        """
        if not self._initialized:
            return
        if self.filters:
            self._apply_filters()
        pygame.display.flip()

    def _apply_filters(self) -> None:
        """Stack and apply all active filters to the screen (or to the filter framebuffer)."""
        if not self.filters or not self.filter_shader.program:
            return

        # Update filter animations
        for f in self.filters:
            if f.enabled:
                f.update(1.0 / 60.0)

        self.filter_shader.use()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._filter_texture)
        glUniform1i(self.filter_shader._get_uniform_location("screenTexture"), 0)
        glUniform2f(self.filter_shader._get_uniform_location("screenSize"), self.width, self.height)

        # Mapping from FilterType to integer IDs (matching shader)
        filter_type_map = {
            FilterType.NONE: 0,
            FilterType.VIGNETTE: 1,
            FilterType.BLUR: 2,
            FilterType.SEPIA: 3,
            FilterType.GRAYSCALE: 4,
            FilterType.INVERT: 5,
            FilterType.TEMPERATURE_WARM: 6,
            FilterType.TEMPERATURE_COLD: 7,
            FilterType.NIGHT_VISION: 8,
            FilterType.CRT: 9,
            FilterType.PIXELATE: 10,
            FilterType.BLOOM: 11,
            FilterType.EDGE_DETECT: 12,
            FilterType.EMBOSS: 13,
            FilterType.SHARPEN: 14,
            FilterType.POSTERIZE: 15,
            FilterType.NEON: 16,
            FilterType.RADIAL_BLUR: 17,
            FilterType.FISHEYE: 18,
            FilterType.TWIRL: 19,
        }

        for f in self.filters:
            if not f.enabled:
                continue

            filter_id = filter_type_map.get(f.filter_type, 0)
            glUniform1i(self.filter_shader._get_uniform_location("filterType"), filter_id)
            glUniform1f(self.filter_shader._get_uniform_location("intensity"), f.intensity)
            glUniform1f(self.filter_shader._get_uniform_location("time"), f.time)

            region_type_map = {
                FilterRegionType.FULLSCREEN: 0,
                FilterRegionType.RECTANGLE: 1,
                FilterRegionType.CIRCLE: 2,
            }
            glUniform1i(self.filter_shader._get_uniform_location("regionType"),
                        region_type_map.get(f.region_type, 0))
            glUniform4f(self.filter_shader._get_uniform_location("regionParams"),
                        f.region_pos[0], f.region_pos[1],
                        f.region_size[0], f.region_size[1])
            glUniform1f(self.filter_shader._get_uniform_location("radius"), f.radius)
            glUniform1f(self.filter_shader._get_uniform_location("feather"), f.feather)

            glBindVertexArray(self.filter_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        self.filter_shader.unuse()

        # Restore default framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    # ========================================================================
    # Surface and Texture Management
    # ========================================================================

    def get_surface(self) -> pygame.Surface:
        """Return the main display surface (created by pygame)."""
        return pygame.display.get_surface()

    def set_surface(self, surface: Optional[pygame.Surface]) -> None:
        """
        Redirect rendering to a custom pygame surface (using a framebuffer).

        Args:
            surface: Target surface, or None to reset to the main display.
        """
        if surface == self._current_target:
            return
        if surface is None:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            self.width, self.height = self.get_surface().get_size()
        else:
            tex_id = self._surface_to_texture(surface)
            fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex_id, 0)
            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                print("Framebuffer not complete!")
                glBindFramebuffer(GL_FRAMEBUFFER, 0)
                return
            self.width, self.height = surface.get_size()
        self._current_target = surface

    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        """
        Convert a pygame Surface into an OpenGL texture (without caching).

        Args:
            surface: Source surface (should have alpha channel for best results).

        Returns:
            OpenGL texture ID.
        """
        if surface.get_bytesize() != 4 or not (surface.get_flags() & pygame.SRCALPHA):
            converted = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
            converted.blit(surface, (0, 0))
            surface = converted

        w, h = surface.get_size()
        data = pygame.image.tostring(surface, 'RGBA', False)

        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        return tex

    def _surface_to_texture_cached(self, surface: pygame.Surface,
                                   rect: Optional[pygame.Rect] = None,
                                   dest: Optional[pygame.Rect] = None,
                                   flags: int = 0) -> int:
        """
        Convert a surface to a texture, with caching based on the surface object itself.
        Uses weak references to avoid retaining surfaces after they are garbage‑collected.

        Args:
            surface: Source surface.
            rect: Optional source rectangle (cropping).
            dest: Optional destination rectangle (ignored for caching, but kept for key).
            flags: Additional flags that affect texture generation.

        Returns:
            OpenGL texture ID (cached).
        """
        # Build a hashable sub‑key from rect, dest, and flags
        rect_data = None
        if rect is not None:
            if isinstance(rect, pygame.Rect):
                rect_data = (rect.x, rect.y, rect.w, rect.h)
            else:
                rect_data = tuple(rect)  # assume a 4‑tuple

        dest_data = None
        if dest is not None:
            if isinstance(dest, pygame.Rect):
                dest_data = (dest.x, dest.y, dest.w, dest.h)
            else:
                dest_data = tuple(dest)

        sub_key = (rect_data, dest_data, flags)

        # Get the inner dict for this specific surface, or create it
        surf_cache = self._texture_cache.get(surface)
        if surf_cache is None:
            surf_cache = {}
            self._texture_cache[surface] = surf_cache

        # Check if we already have a texture for this sub‑key
        if sub_key in surf_cache:
            tex, size, last_use = surf_cache[sub_key]
            # Safety check: if the surface size has changed, we need a new texture
            if size == surface.get_size():
                return tex

        # Generate a new texture
        tex = self._surface_to_texture(surface)
        surf_cache[sub_key] = (tex, surface.get_size(), time.time())
        return tex

    def _convert_color(self, color: Union[Tuple[int, int, int, float], Tuple[int, int, int], Tuple[float, float, float, float], Color, ThemeStyle]) -> Tuple[float, float, float, float]:
        """
        Normalise a colour to (r, g, b, a) floats in [0, 1].

        Args:
            color: Colour as (r, g, b) or (r, g, b, a) with values 0‑255 or 0‑1 (alpha 0‑255 also allowed).

        Returns:
            Normalised (r, g, b, a) where each component is in [0, 1].
        """
        if isinstance(color, Color):
            r, g, b, a = color.r, color.g, color.b, color.a
        elif isinstance(color, ThemeStyle):
            r, g, b = color.color
            a = color.alpha
        else:
            if len(color) == 3:
                r, g, b = color
                a = 1.0
            else:
                r, g, b, a = color
        if a > 1.0:
            a /= 255.0
        r = max(0, min(255, int(r))) / 255.0
        g = max(0, min(255, int(g))) / 255.0
        b = max(0, min(255, int(b))) / 255.0
        return (r, g, b, a)

    # ========================================================================
    # Scissor
    # ========================================================================

    def enable_scissor(self, x: int | float, y: int | float,
                       width: int | float, height: int | float) -> None:
        """Push a scissor rectangle, intersecting with any existing one."""
        if not self._initialized:
            return
        x, y, width, height = int(x), int(y), abs(int(width)), abs(int(height))
        # Convert to OpenGL coords (bottom‑left origin)
        gl_y = self.height - (y + height)
        rect = (x, gl_y, width, height)

        if self._scissor_stack:
            prev = self._scissor_stack[-1]
            # Intersect with previous
            ix = max(prev[0], rect[0])
            iy = max(prev[1], rect[1])
            iw = min(prev[0] + prev[2], rect[0] + rect[2]) - ix
            ih = min(prev[1] + prev[3], rect[1] + rect[3]) - iy
            if iw <= 0 or ih <= 0:
                # Empty intersection – set zero‑size scissor to clip everything
                glEnable(GL_SCISSOR_TEST)
                glScissor(0, 0, 0, 0)
                self._scissor_stack.append((ix, iy, iw, ih))  # store empty rect
                return
            rect = (ix, iy, iw, ih)

        glEnable(GL_SCISSOR_TEST)
        glScissor(rect[0], rect[1], rect[2], rect[3])
        self._scissor_stack.append(rect)

    def disable_scissor(self) -> None:
        """Pop the top scissor rectangle and restore the previous one."""
        if not self._initialized or not self._scissor_stack:
            return
        self._scissor_stack.pop()
        if self._scissor_stack:
            prev = self._scissor_stack[-1]
            if prev[2] <= 0 or prev[3] <= 0:
                # Keep scissor enabled with zero size
                glEnable(GL_SCISSOR_TEST)
                glScissor(prev[0], prev[1], prev[2], prev[3])
            else:
                glEnable(GL_SCISSOR_TEST)
                glScissor(prev[0], prev[1], prev[2], prev[3])
        else:
            glDisable(GL_SCISSOR_TEST)
    
    # ========================================================================
    # Drawing Primitives
    # ========================================================================

    def draw_rect(self, x: int| float, y: int | float, width: int | float, height: int | float,
                  color: Union[Tuple[int, int, int, float], Tuple[int, int, int], Color, Tuple[float, float, float, float], ThemeStyle], fill: bool = True, pivot: tuple = (0.0, 0.0),
                  border_width: int = 1, surface: Optional[pygame.Surface] = None,
                  corner_radius: Union[int, float, Tuple[int, int, int, int], Tuple[float, float, float, float]] = 0,
                  border_color: Optional[Union[Tuple[int, int, int, float], Tuple[int, int, int], Color, Tuple[float, float, float, float], ThemeStyle]] = None) -> None:
        """
        Draw a rectangle with optional fill, border, and rounded corners.

        Args:
            x, y: Position (before anchor adjustment).
            width, height: Rectangle dimensions.
            color: Fill colour (if fill=True).
            fill: If True, filled rectangle; otherwise outline only.
            pivot: Anchor as (fx, fy) where (0,0) is top‑left, (1,1) bottom‑right.
            border_width: Thickness of the border in pixels (used when border_color provided or fill=False).
            surface: Optional target surface (defaults to current render target).
            corner_radius: Radius for all corners (int) or per‑corner (top‑left, top‑right, bottom‑right, bottom‑left).
            border_color: Colour of the border (if None and fill=False, uses `color` for outline).
        """
        if not self._initialized:
            return

        x = x - int(pivot[0] * width)
        y = y - int(pivot[1] * height)

        if surface:
            old = self._current_target
            self.set_surface(surface)

        # Normalise corner radii
        if isinstance(corner_radius, (int, float)) and corner_radius > 0:
            radii = (corner_radius, corner_radius, corner_radius, corner_radius)
        elif isinstance(corner_radius, (tuple, list)) and any(r > 0 for r in corner_radius):
            if len(corner_radius) == 1:
                radii = (corner_radius[0], corner_radius[0], corner_radius[0], corner_radius[0])
            elif len(corner_radius) == 2:
                radii = (corner_radius[0], corner_radius[1], corner_radius[0], corner_radius[1])
            elif len(corner_radius) == 3:
                radii = (corner_radius[0], corner_radius[1], corner_radius[2], corner_radius[1])
            else:
                radii = (corner_radius[0], corner_radius[1], corner_radius[2], corner_radius[3])
        else:
            radii = (0, 0, 0, 0)

        # Outline only
        if not fill:
            self._draw_outline_rect(x, y, width, height, color, border_width, radii)
            if surface:
                self.set_surface(old)
            return

        # Filled with border
        if border_color is not None and border_width > 0:
            # Draw border rectangle (slightly larger)
            border_w = border_width * 2
            border_h = border_width * 2
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(x - border_width, y - border_width,
                                      width + border_w, height + border_h,
                                      border_color, fill=True, border_width=0)
            else:
                expanded_radii = tuple(r + border_width for r in radii)
                self._draw_rounded_rect(x - border_width, y - border_width,
                                        width + border_w, height + border_h,
                                        border_color, fill=True,
                                        border_width=0, radii=expanded_radii)
            # Inner filled rectangle
            inner_x = x + border_width
            inner_y = y + border_width
            inner_w = width - border_w
            inner_h = height - border_h
            if inner_w > 0 and inner_h > 0:
                if all(r == 0 for r in radii):
                    self._draw_sharp_rect(inner_x, inner_y, inner_w, inner_h,
                                          color, fill=True, border_width=0)
                else:
                    inner_radii = tuple(max(0, r - border_width) for r in radii)
                    self._draw_rounded_rect(inner_x, inner_y, inner_w, inner_h,
                                            color, fill=True, border_width=0,
                                            radii=inner_radii)
        else:
            # No border, just fill
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(x, y, width, height, color, fill=True, border_width=0)
            else:
                self._draw_rounded_rect(x, y, width, height, color, fill=True,
                                        border_width=0, radii=radii)

        if surface:
            self.set_surface(old)

    def draw_isosceles_triangle(self, x: int | float, y: int | float,
                            width: int | float, height: int | float,
                            color: Union[Tuple[int, int, int, float], Tuple[int, int, int], Color, Tuple[float, float, float, float], ThemeStyle],
                            fill: bool = True, border_width: int = 1,
                            border_color: Optional[Union[Tuple[int, int, int, float], Tuple[int, int, int], Color, Tuple[float, float, float, float], ThemeStyle]] = None) -> None:
        """
        Draw an isosceles triangle with a horizontal base at the bottom.

        The triangle is defined by a bounding box:
            top vertex at (x + width/2, y)
            bottom-left at (x, y + height)
            bottom-right at (x + width, y + height)

        Args:
            x, y: Top‑left corner of the bounding box.
            width, height: Bounding box dimensions.
            color: Fill colour (if fill=True) or outline colour (if no border_color).
            fill: If True, fills the triangle; otherwise draws only the outline.
            border_width: Thickness of the outline (used when fill=False or border_color given).
            border_color: Colour for the outline; if provided, an outline is drawn
                        on top of the fill (if fill=True) or as the only outline
                        (if fill=False). If None and fill=False, `color` is used.
        """
        if not self._initialized:
            return

        # Compute the three vertices (isosceles, apex up)
        vertices = [
            (x + width / 2.0, y),          # apex
            (x, y + height),               # bottom-left
            (x + width, y + height)        # bottom-right
        ]

        # Draw fill if requested
        if fill:
            self.draw_polygon(vertices, color, fill=True, border_width=0)

        # Draw outline if border_color is provided, or if fill=False (use color)
        if border_color is not None:
            # Outline with explicit border color
            self.draw_polygon(vertices, border_color, fill=False, border_width=border_width)
        elif not fill:
            # Outline with the given color
            self.draw_polygon(vertices, color, fill=False, border_width=border_width)
        # If fill=True and border_color is None, no outline is drawn


    def draw_equilateral_triangle(self, x: int | float, y: int | float,
                                width: int | float,
                                color: Union[Tuple[int, int, int, float], Tuple[int, int, int], Color, Tuple[float, float, float, float], ThemeStyle],
                                fill: bool = True, border_width: int = 1,
                                border_color: Optional[Union[Tuple[int, int, int, float], Tuple[int, int, int], Color, Tuple[float, float, float, float], ThemeStyle]] = None) -> None:
        """
        Draw an equilateral triangle with a horizontal base at the bottom.

        The triangle is defined by the side length `width`. The bounding box
        has width = side length and height = side * sqrt(3)/2, with top-left at (x, y).

        Args:
            x, y: Top‑left corner of the bounding box.
            width: Side length of the equilateral triangle.
            color: Fill colour (if fill=True) or outline colour (if no border_color).
            fill: If True, fills the triangle; otherwise draws only the outline.
            border_width: Thickness of the outline (used when fill=False or border_color given).
            border_color: Colour for the outline; if provided, an outline is drawn
                        on top of the fill (if fill=True) or as the only outline
                        (if fill=False). If None and fill=False, `color` is used.
        """
        if not self._initialized:
            return

        # Equilateral triangle: side = width, height = side * sqrt(3)/2
        side = float(width)
        height = side * math.sqrt(3.0) / 2.0

        vertices = [
            (x + side / 2.0, y),          # apex
            (x, y + height),              # bottom-left
            (x + side, y + height)        # bottom-right
        ]

        # Draw fill if requested
        if fill:
            self.draw_polygon(vertices, color, fill=True, border_width=0)

        # Draw outline if border_color is provided, or if fill=False (use color)
        if border_color is not None:
            self.draw_polygon(vertices, border_color, fill=False, border_width=border_width)
        elif not fill:
            self.draw_polygon(vertices, color, fill=False, border_width=border_width)

    def _draw_outline_rect(self, x: int, y: int, width: int, height: int,
                           color: tuple, border_width: int, radii: Tuple[int, int, int, int]) -> None:
        """Internal: draw only the outline of a rectangle."""
        if all(r == 0 for r in radii):
            self._draw_sharp_rect(x, y, width, height, color, fill=False, border_width=border_width)
        else:
            self._draw_rounded_rect(x, y, width, height, color, fill=False,
                                    border_width=border_width, radii=radii)

    def _draw_sharp_rect(self, x: int, y: int, width: int, height: int,
                         color: tuple, fill: bool = True, border_width: int = 1) -> None:
        """Internal: draw a rectangle without rounded corners (sharp)."""
        self.simple_shader.use()
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"),
                    float(self.width), float(self.height))
        r, g, b, a = self._convert_color(color)

        if not fill:
            # Draw four thin rectangles for the border
            self._draw_sharp_rect(x, y, width, border_width, color, fill=True, border_width=0)
            self._draw_sharp_rect(x, y + height - border_width, width, border_width, color, fill=True, border_width=0)
            self._draw_sharp_rect(x, y + border_width, border_width, height - 2 * border_width, color, fill=True, border_width=0)
            self._draw_sharp_rect(x + width - border_width, y + border_width, border_width, height - 2 * border_width, color, fill=True, border_width=0)
        else:
            glUniform4f(self.simple_shader._get_uniform_location("uTransform"),
                        float(x), float(y), float(width), float(height))
            glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)
            glBindVertexArray(self.simple_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

        self.simple_shader.unuse()

    def _draw_rounded_rect(self, x: int, y: int, w: int, h: int, color: tuple,
                           fill: bool = True, border_width: int = 1, radii: Tuple[int, int, int, int] = (0, 0, 0, 0)) -> None:
        """Internal: draw a rounded rectangle (filled or outline) using the rounded rect shader."""
        r, g, b, a = self._convert_color(color)
        self.rounded_rect_shader.use()
        glUniform2f(self.rounded_rect_shader._get_uniform_location("uScreenSize"),
                    self.width, self.height)
        glUniform4f(self.rounded_rect_shader._get_uniform_location("uTransform"), x, y, w, h)
        glUniform4f(self.rounded_rect_shader._get_uniform_location("uColor"), r, g, b, a)
        glUniform4f(self.rounded_rect_shader._get_uniform_location("uCornerRadii"),
                    float(radii[0]), float(radii[1]), float(radii[2]), float(radii[3]))
        glUniform2f(self.rounded_rect_shader._get_uniform_location("uRectSize"), w, h)
        glUniform1f(self.rounded_rect_shader._get_uniform_location("uFeather"), 1.5)
        glUniform1i(self.rounded_rect_shader._get_uniform_location("uFill"), 1 if fill else 0)
        glUniform1f(self.rounded_rect_shader._get_uniform_location("uBorderWidth"), border_width if not fill else 0)

        glBindVertexArray(self.rounded_rect_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        self.rounded_rect_shader.unuse()

    def draw_line(self, start_x: int | float, start_y: int | float,
                  end_x: int | float, end_y: int | float,
                  color: tuple, width: int = 2, surface: Optional[pygame.Surface] = None) -> None:
        """
        Draw a thick line between two points.

        Args:
            start_x, start_y: Start point.
            end_x, end_y: End point.
            color: RGB or RGBA colour.
            width: Line thickness in pixels.
            surface: Optional target surface.
        """
        if not self._initialized or not self.simple_shader.program:
            return
        if surface:
            old = self._current_target
            self.set_surface(surface)

        if start_x == end_x and start_y == end_y:
            return

        self._draw_thick_line(start_x, start_y, end_x, end_y, color, width)

        if surface:
            self.set_surface(old)

    def _draw_thick_line(self, x1: float, y1: float, x2: float, y2: float,
                         color: tuple, width: float) -> None:
        """Internal: draw a line by creating a quad perpendicular to the direction."""
        r, g, b, a = self._convert_color(color)
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            return
        dx /= length
        dy /= length
        perp_x = -dy * (width / 2)
        perp_y = dx * (width / 2)

        vertices = np.array([
            x1 + perp_x, y1 + perp_y,
            x1 - perp_x, y1 - perp_y,
            x2 - perp_x, y2 - perp_y,
            x2 + perp_x, y2 + perp_y,
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        ebo = glGenBuffers(1)

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self.simple_shader.use()
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 0, 0, 1, 1)
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)

        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        glDeleteVertexArrays(1, [vao])
        glDeleteBuffers(1, [vbo])
        glDeleteBuffers(1, [ebo])
        self.simple_shader.unuse()

    def draw_lines(self, points: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                   color: tuple, width: int = 2, surface: Optional[pygame.Surface] = None) -> None:
        """
        Draw multiple line segments.

        Args:
            points: List of ((x1,y1), (x2,y2)) pairs.
            color: Line colour.
            width: Line thickness.
            surface: Optional target surface.
        """
        for (x1, y1), (x2, y2) in points:
            self.draw_line(x1, y1, x2, y2, color, width, surface)

    def draw_circle(self, center_x: int | float, center_y: int | float, radius: int | float,
                    color: tuple, fill: bool = True, border_width: int = 1,
                    surface: Optional[pygame.Surface] = None,
                    pivot: Tuple[float, float] = (0.5, 0.5)) -> None:
        """
        Draw a circle (filled or outline) with caching.

        Args:
            center_x, center_y: Centre position (before anchor).
            radius: Circle radius.
            color: Fill or outline colour.
            fill: If True, filled circle; otherwise outline.
            border_width: Thickness of outline (used when fill=False).
            surface: Optional target surface.
            pivot: Anchor point for positioning (default centre).
        """
        if not self._initialized or not self.simple_shader.program:
            return

        if surface:
            old = self._current_target
            self.set_surface(surface)

        width = radius * 2
        height = radius * 2
        x = center_x - int(pivot[0] * width)
        y = center_y - int(pivot[1] * height)

        cache_key = (radius, fill, border_width)
        if cache_key in self._circle_cache:
            vao, vbo, ebo, vertex_count = self._circle_cache[cache_key]
        else:
            segments = max(24, min(128, radius // 2))
            if fill:
                vertices, indices = self._generate_filled_circle_geometry(segments)
            else:
                vertices, indices = self._generate_hollow_circle_geometry(segments, border_width, radius)
            vao, vbo, ebo = self._upload_geometry(vertices, indices)
            vertex_count = len(indices)
            self._circle_cache[cache_key] = (vao, vbo, ebo, vertex_count)

        r, g, b, a = self._convert_color(color)
        self.simple_shader.use()
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), x, y, width, height)
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)

        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        self.simple_shader.unuse()

        if surface:
            self.set_surface(old)

    def _generate_filled_circle_geometry(self, segments: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate vertex and index arrays for a filled circle (unit coordinates)."""
        segments = int(segments)
        vertices = [0.5, 0.5]
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            vertices.extend([
                math.cos(angle) * 0.5 + 0.5,
                math.sin(angle) * 0.5 + 0.5
            ])
        indices = []
        for i in range(1, segments):
            indices.extend([0, i, i + 1])
        indices.extend([0, segments, 1])
        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)

    def _generate_hollow_circle_geometry(self, segments: int, border_width: float, radius: float) -> Tuple[np.ndarray, np.ndarray]:
        """Generate geometry for a hollow circle (outline) as a single triangle strip."""
        segments = int(segments)
        inner_radius = max(0.1, (radius - border_width) / radius * 0.5)
        outer_radius = 0.5
        vertices = []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            # outer
            vertices.extend([math.cos(angle) * outer_radius + 0.5, math.sin(angle) * outer_radius + 0.5])
            # inner
            vertices.extend([math.cos(angle) * inner_radius + 0.5, math.sin(angle) * inner_radius + 0.5])
        indices = []
        for i in range(segments):
            outer_cur = i * 2
            inner_cur = i * 2 + 1
            outer_next = ((i + 1) % segments) * 2
            inner_next = ((i + 1) % segments) * 2 + 1
            indices.extend([outer_cur, inner_cur, outer_next])
            indices.extend([inner_cur, inner_next, outer_next])
        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)

    def _upload_geometry(self, vertices: np.ndarray, indices: np.ndarray) -> Tuple[int, int, int]:
        """Create VAO, VBO, EBO and upload vertex/index data. Returns (vao, vbo, ebo)."""
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        ebo = glGenBuffers(1)

        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)

        return vao, vbo, ebo

    def draw_polygon(self, points: List[Tuple[float, float]], color: tuple,
                     fill: bool = True, border_width: int = 1,
                     surface: Optional[pygame.Surface] = None,
                     pivot: Tuple[float, float] = (0.0, 0.0)) -> None:
        """
        Draw a convex polygon (filled or outline).

        Args:
            points: List of (x, y) vertices.
            color: Fill or outline colour.
            fill: If True, filled polygon; otherwise outline.
            border_width: Outline thickness (only used when fill=False).
            surface: Optional target surface.
            pivot: Offset applied to all points.
        """
        if not self._initialized or len(points) < 3:
            return

        if surface:
            old = self._current_target
            self.set_surface(surface)

        # Adjust points by anchor
        points = [(x + pivot[0], y + pivot[1]) for x, y in points]

        if fill:
            vertices, indices = self._generate_filled_polygon_geometry(points)
        else:
            vertices, indices = self._generate_hollow_polygon_geometry(points, border_width)

        vao, vbo, ebo = self._upload_geometry(vertices, indices)
        vertex_count = len(indices)

        xs, ys = zip(*points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width, height = max_x - min_x, max_y - min_y

        r, g, b, a = self._convert_color(color)
        self.simple_shader.use()
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), min_x, min_y, width, height)
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)

        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        glDeleteVertexArrays(1, [vao])
        glDeleteBuffers(1, [vbo])
        glDeleteBuffers(1, [ebo])
        self.simple_shader.unuse()

        if surface:
            self.set_surface(old)

    def _generate_filled_polygon_geometry(self, points: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Generate triangulation for a filled polygon (assumes convex)."""
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)

        vertices = []
        for x, y in points:
            vertices.append((x - min_x) / w)
            vertices.append((y - min_y) / h)

        indices = []
        for i in range(1, len(points) - 1):
            indices.extend([0, i, i + 1])

        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)

    def _generate_hollow_polygon_geometry(self, points: List[Tuple[float, float]], border_width: float) -> Tuple[np.ndarray, np.ndarray]:
        """Generate geometry for a hollow polygon outline."""
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)

        offset_x = border_width / w
        offset_y = border_width / h

        vertices = []
        for x, y in points:
            nx = (x - min_x) / w
            ny = (y - min_y) / h
            vertices.extend([nx, ny])
            # inner point toward centre
            center_x, center_y = 0.5, 0.5
            dx = nx - center_x
            dy = ny - center_y
            length = max(0.001, math.hypot(dx, dy))
            dx /= length
            dy /= length
            vertices.extend([nx - dx * offset_x, ny - dy * offset_y])

        indices = []
        n = len(points)
        for i in range(n):
            next_i = (i + 1) % n
            outer_cur = i * 2
            inner_cur = i * 2 + 1
            outer_next = next_i * 2
            inner_next = next_i * 2 + 1
            indices.extend([outer_cur, inner_cur, outer_next])
            indices.extend([inner_cur, inner_next, outer_next])

        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)

    def draw_text(self, text: str, x: int, y: int, color,
                  font: pygame.font.Font, surface: Optional[pygame.Surface] = None,
                  pivot: Tuple[float, float] = (0.0, 0.0),
                  flip: Tuple[bool, bool] = (False, False), rotate: float = 0.0,
                  *args, **kwargs) -> None:
        """
        Draw text using a pygame font, with optional flip, rotation, and caching.

        Args:
            text: The string to render.
            x, y: Position (before anchor).
            color: Any colour format accepted (pygame.Color, tuple, etc.).
            font: Pygame font object.
            surface: Optional target surface.
            pivot: Anchor (fx, fy) relative to text size.
            flip: (flip_horizontal, flip_vertical).
            rotate: Rotation angle in degrees (clockwise).
        """
        if not self._initialized:
            return

        # Convert colour to pygame.Color
        try:
            if isinstance(color, pygame.Color):
                pygame_color = color
            elif isinstance(color, Color):
                pygame_color = pygame.Color(color.r, color.g, color.b, int(color.a * 255))
            elif isinstance(color, (tuple, list)):
                if len(color) >= 3:
                    r, g, b = int(color[0]), int(color[1]), int(color[2])
                    a = int(color[3]) if len(color) > 3 else 255
                    pygame_color = pygame.Color(r, g, b, a)
                else:
                    pygame_color = pygame.Color(255, 255, 255)
            elif isinstance(color, int):
                pygame_color = pygame.Color(color, color, color)
            else:
                pygame_color = pygame.Color(255, 255, 255)
        except Exception as e:
            print(f"Colour conversion error: {e}, falling back to white")
            pygame_color = pygame.Color(255, 255, 255)

        r, g, b, a = pygame_color.r, pygame_color.g, pygame_color.b, pygame_color.a
        rgba = (r / 255.0, g / 255.0, b / 255.0, a / 255.0)

        # Font style
        is_bold = kwargs.get('bold', False)
        is_italic = kwargs.get('italic', False)
        if isinstance(font, tuple):
            font = pygame.font.SysFont(font[0], font[1], is_bold, is_italic)

        # Cache key
        cache_key = (text, font, (r, g, b), (is_bold, is_italic))
        now = time.time()
        if cache_key in self._text_cache:
            tex, (tw, th) = self._text_cache[cache_key]
            self._text_cache_last_used[cache_key] = now
        else:
            text_surface = font.render(text, True, pygame_color)
            tex = self._surface_to_texture(text_surface)
            tw, th = text_surface.get_size()
            self._text_cache[cache_key] = (tex, (tw, th))
            self._text_cache_last_used[cache_key] = now

        # Cleanup old cache entries
        if now - self._last_text_cache_cleanup >= self._text_cache_cleanup_interval:
            self._cleanup_text_cache(now)

        # Position
        x = x - int(pivot[0] * tw)
        y = y - int(pivot[1] * th)

        old_target = None
        if surface:
            old_target = self._current_target
            self.set_surface(surface)

        # Fast path: no flip/rotate
        if flip == (False, False) and rotate == 0.0:
            self.texture_shader.use()
            glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), self.width, self.height)
            glUniform4f(self.texture_shader._get_uniform_location("uTransform"), x, y, tw, th)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, tex)
            glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
            glBindVertexArray(self.texture_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
            self.texture_shader.unuse()
        else:
            # Slow path: manual quad with flip & rotate
            center_x = x + tw / 2.0
            center_y = y + th / 2.0
            w2, h2 = tw / 2.0, th / 2.0
            corners = [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]
            uvs = [
                (0.0 if not flip[0] else 1.0, 0.0 if not flip[1] else 1.0),
                (1.0 if not flip[0] else 0.0, 0.0 if not flip[1] else 1.0),
                (1.0 if not flip[0] else 0.0, 1.0 if not flip[1] else 0.0),
                (0.0 if not flip[0] else 1.0, 1.0 if not flip[1] else 0.0)
            ]
            if rotate != 0.0:
                rad = math.radians(rotate)
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                corners = [(cx * cos_a - cy * sin_a, cx * sin_a + cy * cos_a) for (cx, cy) in corners]

            vertices = []
            for (cx, cy), (u, v) in zip(corners, uvs):
                vertices.extend([center_x + cx, center_y + cy, u, v])

            vertices_arr = np.array(vertices, dtype=np.float32)
            indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

            vao = glGenVertexArrays(1)
            vbo = glGenBuffers(1)
            ebo = glGenBuffers(1)

            glBindVertexArray(vao)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices_arr.nbytes, vertices_arr, GL_STATIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices_arr.itemsize, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices_arr.itemsize,
                                  ctypes.c_void_p(2 * vertices_arr.itemsize))
            glEnableVertexAttribArray(1)

            self.texture_shader.use()
            glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), self.width, self.height)
            glUniform4f(self.texture_shader._get_uniform_location("uTransform"), 0.0, 0.0, 1.0, 1.0)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, tex)
            glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)

            glBindVertexArray(vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
            glDeleteBuffers(1, [ebo])
            self.texture_shader.unuse()

        if surface:
            self.set_surface(old_target)

    # ========================================================================
    # Rich Text Wrappers (delegate to labels module)
    # ========================================================================

    def draw_rich_text(self, text: str, x: int, y: int, default_color,
                       font: pygame.font.Font, surface: Optional[pygame.Surface] = None,
                       pivot: Tuple[float, float] = (0.0, 0.0),
                       **kwargs) -> None:
        """
        Draw rich text using the rich text parser.

        Args:
            text: Rich text string with markup
            x, y: Position
            default_color: Default text color (can be Color, ThemeStyle, or tuple)
            font: Base font
            surface: Optional target surface
            pivot: Anchor point
            **kwargs: Additional arguments for draw_text
        """
        if not text:
            return

        # Local import to avoid circular dependency
        from ..ui.elements.labels import render_rich_text

        render_rich_text(text, self, x, y, default_color, font, pivot, **kwargs)

    def draw_rich_text_line(self, line: List['RichTextSegment'], x: int, y: int,
                            default_color, font: pygame.font.Font,
                            surface: Optional[pygame.Surface] = None) -> None:
        """
        Draw a pre-parsed rich text line.

        Args:
            line: List of RichTextSegment objects
            x, y: Position
            default_color: Default text color (can be Color, ThemeStyle, or tuple)
            font: Base font
            surface: Optional target surface
        """
        if not line:
            return

        from ..ui.elements.labels import render_rich_text_line

        render_rich_text_line(line, self, x, y, default_color, font)

    def _cleanup_text_cache(self, now: float) -> None:
        """Remove text textures that have not been used for longer than the timeout."""
        keys_to_delete = []
        for key, last_used in self._text_cache_last_used.items():
            if now - last_used > self._text_cache_timeout:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            tex, _ = self._text_cache.pop(key, (None, None))
            if tex:
                glDeleteTextures(1, [tex])
            self._text_cache_last_used.pop(key, None)

        self._last_text_cache_cleanup = now

    # ========================================================================
    # FIXED TEXTURE CACHE CLEANUP
    # ========================================================================

    def _cleanup_texture_cache(self, time_dur: float = 5.0, force_cleanup: bool = False) -> None:
        """
        Remove expired textures from the weakref‑based texture cache.

        This iterates over all live surfaces and removes textures that have not
        been used for longer than `time_dur` (or all, if `force_cleanup` is True).

        Args:
            time_dur: Age threshold in seconds.
            force_cleanup: If True, delete all textures regardless of age.
        """
        now = time.time()
        # Skip if not forced and not enough time has passed
        if not force_cleanup and (now - self._last_texture_cache_cleanup < self._texture_cache_timeout):
            return

        # Iterate over a snapshot of the live surface entries
        for surface, inner_cache in list(self._texture_cache.items()):
            expired_sub_keys = []
            for sub_key, (tex, size, last_use) in inner_cache.items():
                if force_cleanup or (now - last_use > time_dur):
                    glDeleteTextures(1, [tex])
                    expired_sub_keys.append(sub_key)
            # Remove expired entries
            for key in expired_sub_keys:
                del inner_cache[key]
            # If the inner cache becomes empty, remove the surface entry entirely
            if not inner_cache:
                # The weakref will also drop it, but we can delete it explicitly
                del self._texture_cache[surface]

        self._last_texture_cache_cleanup = now

    # ------------------------------------------------------------------------
    # Surface blitting (with anchor support)
    # ------------------------------------------------------------------------

    def draw_surface(self, surface: pygame.Surface, x: int, y: int,
                 pivot: Tuple[float, float] = (0.0, 0.0),
                 use_cache: bool = True) -> None:
        """Alias for blit with optional cache control."""
        self.blit(surface, (x, y), pivot=pivot, use_cache=use_cache)

    def blit(self, source: pygame.Surface, dest: Union[Tuple[int, int], pygame.Rect],
         area: Optional[pygame.Rect] = None, special_flags: int = 0,
         pivot: Tuple[float, float] = (0.0, 0.0),
         use_cache: bool = True) -> None:
        if not self._initialized or not self.texture_shader.program:
            return

        src_w, src_h = source.get_size()

        if isinstance(dest, pygame.Rect):
            x, y, dest_w, dest_h = dest.x, dest.y, dest.w, dest.h
        else:
            x, y = dest
            dest_w, dest_h = src_w, src_h

        if area:
            source = source.subsurface(area)
            src_w, src_h = area.width, area.height

        x = x - int(pivot[0] * dest_w)
        y = y - int(pivot[1] * dest_h)
        self._cleanup_texture_cache()

        if use_cache:
            tex = self._surface_to_texture_cached(source, area, dest, special_flags)
        else:
            tex = self._surface_to_texture(source)

        self.texture_shader.use()
        glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        glUniform4f(self.texture_shader._get_uniform_location("uTransform"), x, y, dest_w, dest_h)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex)
        glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindVertexArray(self.texture_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        self.texture_shader.unuse()
    
    def fill_screen(self, color: Tuple[int, int, int, float]|Tuple[int, int, int]) -> None:
        """
        Fill the entire screen (or current framebuffer) with a solid colour.

        Args:
            color: RGBA tuple with components 0‑255 (RGB) and alpha 0‑1, or RGB tuple with components 0‑255.
        """
        r, g, b, a = self._convert_color(color)
        glClearColor(r, g, b, a)
        glClear(GL_COLOR_BUFFER_BIT)

    def clear(self) -> None:
        """Clear the colour and depth buffers."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # ========================================================================
    # Particle Rendering
    # ========================================================================

    def render_particles(self, particle_data: Dict[str, Any], camera: Any) -> None:
        """
        Render particle system using instancing.

        Args:
            particle_data: Dictionary with keys:
                - 'active_count': number of active particles
                - 'positions': numpy array (N,2) world positions
                - 'sizes': numpy array (N,) sizes (world units)
                - 'colors': numpy array (N,3) uint8 RGB
                - 'alphas': numpy array (N,) uint8 alpha
            camera: Camera object that provides world_to_screen and convert_size_zoom.
        """
        if not self._initialized or not self.particle_shader.program:
            return

        active = particle_data['active_count']
        if active == 0:
            return

        self._ensure_particle_capacity(active)

        # Convert world positions to screen positions
        world_pos = particle_data['positions']
        screen_pos = np.zeros((active, 2), dtype=np.float32)
        for i in range(active):
            sp = camera.world_to_screen(world_pos[i])
            screen_pos[i] = [sp.x, sp.y]

        sizes = camera.convert_size_zoom_list(particle_data['sizes'][:active], 'ndarray')
        alphas = particle_data['alphas'][:active] / 255.0
        colors = particle_data['colors'][:active] / 255.0

        # Instance data: x, y, size, alpha
        instance_data = np.zeros((active, 4), dtype=np.float32)
        instance_data[:, 0] = screen_pos[:, 0]
        instance_data[:, 1] = screen_pos[:, 1]
        instance_data[:, 2] = np.maximum(2.0, sizes)
        instance_data[:, 3] = alphas

        colour_data = np.zeros((active, 4), dtype=np.float32)
        colour_data[:, 0:3] = colors
        colour_data[:, 3] = 1.0

        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_data.nbytes, instance_data, GL_DYNAMIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, colour_data.nbytes, colour_data, GL_DYNAMIC_DRAW)

        self.particle_shader.use()
        glUniform2f(self.particle_shader._get_uniform_location("uScreenSize"), self.width, self.height)

        glBindVertexArray(self.particle_shader.vao)
        glDrawArraysInstanced(GL_POINTS, 0, 1, active)
        glBindVertexArray(0)

        self.particle_shader.unuse()

    def _ensure_particle_capacity(self, required: int) -> None:
        """Resize instance buffers if needed to accommodate `required` particles."""
        if required <= self._max_particles:
            return
        # Next power of two
        new_size = 1
        while new_size < required:
            new_size *= 2

        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        glBufferData(GL_ARRAY_BUFFER, new_size * 4 * 4, None, GL_DYNAMIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, new_size * 4 * 4, None, GL_DYNAMIC_DRAW)

        self._max_particles = new_size

    # ========================================================================
    # Cleanup
    # ========================================================================

    def cleanup(self) -> None:
        """Release all OpenGL resources (shaders, textures, buffers, framebuffers)."""
        if not self._initialized:
            return

        # Delete shader programs
        for shader in [self.simple_shader, self.texture_shader, self.particle_shader,
                       self.filter_shader, self.rounded_rect_shader]:
            if shader and shader.program:
                glDeleteProgram(shader.program)

        # Delete filter framebuffer
        if self._filter_framebuffer:
            glDeleteFramebuffers(1, [self._filter_framebuffer])
        if self._filter_texture:
            glDeleteTextures(1, [self._filter_texture])
        if self._filter_renderbuffer:
            glDeleteRenderbuffers(1, [self._filter_renderbuffer])

        # Delete geometry caches
        for vao, vbo, ebo, _ in self._circle_cache.values():
            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
            glDeleteBuffers(1, [ebo])
        for vao, vbo, ebo, _ in self._polygon_cache.values():
            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
            glDeleteBuffers(1, [ebo])

        # Delete texture cache (force cleanup all)
        self._cleanup_texture_cache(force_cleanup=True)

        self._circle_cache.clear()
        self._polygon_cache.clear()
        self._texture_cache.clear()
        self._text_cache.clear()

        self._initialized = False

    def set_blend_mode(self, mode: str) -> None:
        """
        Set the OpenGL blending mode.

        Args:
            mode: One of 'normal', 'add', 'multiply', 'screen'.
        """
        if mode == 'normal':
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        elif mode == 'add':
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        elif mode == 'multiply':
            glBlendFunc(GL_DST_COLOR, GL_ZERO)
        elif mode == 'screen':
            glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR)
        else:
            print(f"Unknown blend mode: {mode}")