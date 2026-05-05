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
v0.2.3
"""

import pygame, ctypes, math, os, sys, time
import numpy as np
from typing import Tuple, Dict, Any, List, Optional, Union, Literal
from enum import Enum
from ..utils import math_utils as math_utils
from .types import Color

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
    FULLSCREEN = "fullscreen"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"

class Filter:
    """Simple filter class with all parameters"""
    
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
            filter_type: Type of filter effect
            intensity: Filter strength (0.0 to 1.0)
            region_type: Shape of filter region
            region_pos: Position of region (top-left for rect, center for circle)
            region_size: Size of region (width, height)
            radius: Radius for circular regions
            feather: Edge softness in pixels
            blend_mode: How filter blends with background
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
        
    def update(self, dt: float):
        """Update filter for animation"""
        self.time += dt
        
    def copy(self) -> 'Filter':
        """Create a copy of this filter"""
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
    """Base class for all shader programs with uniform caching."""
    vertex_source:str|None = None
    fragment_source:str|None = None
    geometry_source:str|None = None
    def get_source(self, source: str|None, type:Literal['vertex', 'fragment', 'geometry']):
        shaders_folder = os.path.join(os.path.dirname(__file__),'..','graphics', 'shaders')
        if source and os.path.exists(shaders_folder):
            if os.path.exists(os.path.join(shaders_folder, source)):
                if type == 'vertex':
                    self.vertex_source = str(open(os.path.join(shaders_folder, source), 'r').read())
                elif type == 'fragment':
                    self.fragment_source = str(open(os.path.join(shaders_folder, source), 'r').read())
                elif type == 'geometry':
                    self.geometry_source = str(open(os.path.join(shaders_folder, source), 'r').read())
    
    def __init__(self, vertex_source: str, fragment_source: str, geometry_source: Optional[str] = None):
        self.get_source(vertex_source, 'vertex')
        self.get_source(fragment_source, 'fragment')
        self.get_source(geometry_source, 'geometry')
        self.program = None
        self.vao = None
        self.vbo = None
        self.ebo = None
        self._uniform_locations = {}
        self._create_program(self.vertex_source, self.fragment_source, self.geometry_source)
        if self.program:
            self._setup_geometry()
    
    def _get_uniform_location(self, name: str) -> int:
        """Get cached uniform location."""
        if name not in self._uniform_locations:
            self._uniform_locations[name] = glGetUniformLocation(self.program, name)
        return self._uniform_locations[name]
    
    def _create_program(self, vertex_source: str, fragment_source: str, geometry_source: Optional[str] = None):
        """Compile and link shaders."""
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
    
    def use(self):
        """Activate the shader program."""
        if self.program:
            glUseProgram(self.program)
    
    def unuse(self):
        """Deactivate the shader program."""
        glUseProgram(0)
    
    def _setup_geometry(self):
        """Set up vertex arrays - to be overridden by subclasses."""
        pass

# ============================================================================
# Particle Shader (Instanced)
# ============================================================================

class ParticleShader(ShaderProgram):
    """Instanced particle shader."""
    
    def __init__(self):
        super().__init__(vertex_source='particle.vert', fragment_source='particle.frag')
    
    def _setup_geometry(self):
        """Create a dummy VAO with one vertex (for instancing)."""
        # One dummy vertex (position doesn't matter)
        vertices = np.array([0.0, 0.0], dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)                     # dummy vertex buffer
        self.instance_data_vbo = glGenBuffers(1)       # x,y,size,alpha per instance
        self.instance_color_vbo = glGenBuffers(1)      # color per instance
        
        glBindVertexArray(self.vao)
        
        # Dummy vertex (location 0)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Instance data (location 1)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_data_vbo)
        # Initial allocation – will be resized dynamically
        glBufferData(GL_ARRAY_BUFFER, 1024 * 4 * 4, None, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribDivisor(1, 1)   # one per instance
        
        # Instance color (location 2)
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
    """Simple shader for solid color rectangles and shapes."""
    
    def __init__(self):
        super().__init__(vertex_source='simple.vert', fragment_source='simple.frag')
    
    def _setup_geometry(self):
        """Setup a unit quad (0,0 to 1,1)."""
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
    """Shader for textured rendering."""
    
    def __init__(self):
        super().__init__(vertex_source='texture.vert', fragment_source='texture.frag')
    
    def _setup_geometry(self):
        """Setup textured quad with UVs."""
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
        
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        glEnableVertexAttribArray(1)
        
        glBindVertexArray(0)

# ============================================================================
# Rounded Rectangle Shader
# ============================================================================

class RoundedRectShader(ShaderProgram):
    """Shader for drawing rectangles with per-corner rounded corners."""
    
    def __init__(self):
        super().__init__(vertex_source='rounded_rect.vert', fragment_source='rounded_rect.frag')
    
    def _setup_geometry(self):
        """Setup quad geometry for rectangle."""
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
    """Shader for applying post-processing filters."""
    
    def __init__(self):
        super().__init__(vertex_source='filter.vert', fragment_source='filter.frag')
    
    def _setup_geometry(self):
        """Setup fullscreen quad for filter rendering."""
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
        
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        glEnableVertexAttribArray(1)
        
        glBindVertexArray(0)

# ============================================================================
# Main OpenGLRenderer
# ============================================================================

class OpenGLRenderer:
    camera_position = pygame.math.Vector2(0, 0)
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._initialized = False
        
        # Shader instances
        self.simple_shader = None
        self.texture_shader = None
        self.particle_shader = None
        self.filter_shader = None
        self.rounded_rect_shader = None
        
        # Particle system integration
        self._max_particles = 1024
        self.on_max_particles_change: List[callable] = []
        
        # Filter system
        self.filters: List[Filter] = []
        self._filter_framebuffer = None
        self._filter_texture = None
        self._filter_renderbuffer = None
        
        # Geometry caches
        self._circle_cache = {}
        self._polygon_cache = {}
        
        # Current render target
        self._current_target = None
        
        # Texture cache
        self._texture_cache = {}
        
        # Text cache    
        self._text_cache = {}
        self._text_cache_last_used = {}          # key -> last access timestamp
        self._text_cache_timeout = 10.0          # seconds before eviction
        self._last_text_cache_cleanup = 0.0      # last cleanup timestamp
        self._text_cache_cleanup_interval = 5.0  # run cleanup at most every 5 seconds
        
    def set_text_cache_timeout(self, seconds: float):
        """Set how long a text texture stays in cache without being used."""
        self._text_cache_timeout = max(0.1, seconds)
    
    def get_cache_usage(self, target:Literal['text', 'texture', 'circle', 'polygon', 'total','all'] = 'all', humanize:bool = False) -> float|Dict[str, float]:
        """Return cache usage as percentage. If target is 'all', returns dict of all caches."""
        if target == 'all':
            return {
                'text': math_utils.humanize_size(sys.getsizeof(self._text_cache, {})) if humanize else sys.getsizeof(self._text_cache, {}),
                'texture': math_utils.humanize_size(sys.getsizeof(self._texture_cache, {})) if humanize else sys.getsizeof(self._texture_cache, {}),
                'circle': math_utils.humanize_size(sys.getsizeof(self._circle_cache, {})) if humanize else sys.getsizeof(self._circle_cache, {}),
                'polygon': math_utils.humanize_size(sys.getsizeof(self._polygon_cache, {})) if humanize else sys.getsizeof(self._polygon_cache, {}),
                'total': self.get_cache_usage('total', humanize)
            }
        elif target == 'text':
            return math_utils.humanize_size(sys.getsizeof(self._text_cache, {})) if humanize else sys.getsizeof(self._text_cache, {})
        elif target == 'texture':
            return math_utils.humanize_size(sys.getsizeof(self._texture_cache, {})) if humanize else sys.getsizeof(self._texture_cache, {})
        elif target == 'circle':
            return math_utils.humanize_size(sys.getsizeof(self._circle_cache, {})) if humanize else sys.getsizeof(self._circle_cache, {})
        elif target == 'polygon':
            return math_utils.humanize_size(sys.getsizeof(self._polygon_cache, {})) if humanize else sys.getsizeof(self._polygon_cache, {})
        elif target == 'total':
            total = (sys.getsizeof(self._text_cache, {}) + sys.getsizeof(self._texture_cache, {}) +
                     sys.getsizeof(self._circle_cache, {}) + sys.getsizeof(self._polygon_cache, {}))
            return math_utils.humanize_size(total) if humanize else total
        else:
            raise ValueError(f"Invalid Cache target: {target}")
    
    @property
    def max_particles(self) -> int:
        return self._max_particles
    
    @max_particles.setter
    def max_particles(self, value: int):
        if value > self._max_particles:
            for callback in self.on_max_particles_change:
                callback(value)
        self._max_particles = value
    
    def initialize(self) -> bool:
        """Initialize OpenGL context and shaders."""
        if not OPENGL_AVAILABLE:
            return False
        
        print(f"Initializing OpenGL renderer for {self.width}x{self.height}...")
        
        # Set up OpenGL state
        glDisable(GL_FRAMEBUFFER_SRGB)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)  # We'll manage depth manually if needed
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
        
        # Initialize filter framebuffer
        self._initialize_filter_framebuffer()
        
        self._initialized = True
        print("OpenGL renderer initialized successfully")
        return True
    
    def _initialize_filter_framebuffer(self) -> bool:
        """Create framebuffer for off-screen filter rendering."""
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
    
    def add_filter(self, filter_obj: Filter):
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: Filter):
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
    
    def clear_filters(self):
        self.filters.clear()
    
    def create_quick_filter(self, filter_type: FilterType, intensity: float = 1.0,
                            x: float = 0, y: float = 0,
                            width: float = None, height: float = None,
                            radius: float = 50.0, feather: float = 10.0) -> Filter:
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
    def apply_vignette(self, intensity=0.7, feather=100.0) -> Filter:
        return self.create_quick_filter(FilterType.VIGNETTE, intensity, feather=feather)
    
    def apply_blur(self, intensity=0.5, x=0, y=0, width=None, height=None) -> Filter:
        return self.create_quick_filter(FilterType.BLUR, intensity, x, y, width, height, feather=20.0)
    
    def apply_sepia(self, intensity=1.0) -> Filter:
        return self.create_quick_filter(FilterType.SEPIA, intensity)
    
    def apply_grayscale(self, intensity=1.0) -> Filter:
        return self.create_quick_filter(FilterType.GRAYSCALE, intensity)
    
    def apply_invert(self, intensity=1.0) -> Filter:
        return self.create_quick_filter(FilterType.INVERT, intensity)
    
    def apply_warm_temperature(self, intensity=0.5) -> Filter:
        return self.create_quick_filter(FilterType.TEMPERATURE_WARM, intensity)
    
    def apply_cold_temperature(self, intensity=0.5) -> Filter:
        return self.create_quick_filter(FilterType.TEMPERATURE_COLD, intensity)
    
    def apply_night_vision(self, intensity=0.9) -> Filter:
        return self.create_quick_filter(FilterType.NIGHT_VISION, intensity)
    
    def apply_crt_effect(self, intensity=0.8) -> Filter:
        return self.create_quick_filter(FilterType.CRT, intensity)
    
    def apply_pixelate(self, intensity=0.7) -> Filter:
        return self.create_quick_filter(FilterType.PIXELATE, intensity)
    
    def apply_bloom(self, intensity=0.5) -> Filter:
        return self.create_quick_filter(FilterType.BLOOM, intensity)
    
    def apply_edge_detect(self, intensity=0.8) -> Filter:
        return self.create_quick_filter(FilterType.EDGE_DETECT, intensity)
    
    def apply_emboss(self, intensity=0.7) -> Filter:
        return self.create_quick_filter(FilterType.EMBOSS, intensity)
    
    def apply_sharpen(self, intensity=0.5) -> Filter:
        return self.create_quick_filter(FilterType.SHARPEN, intensity)
    
    def apply_posterize(self, intensity=0.6) -> Filter:
        return self.create_quick_filter(FilterType.POSTERIZE, intensity)
    
    def apply_neon(self, intensity=0.7) -> Filter:
        return self.create_quick_filter(FilterType.NEON, intensity)
    
    def apply_radial_blur(self, intensity=0.5) -> Filter:
        return self.create_quick_filter(FilterType.RADIAL_BLUR, intensity)
    
    def apply_fisheye(self, intensity=0.4) -> Filter:
        return self.create_quick_filter(FilterType.FISHEYE, intensity)
    
    def apply_twirl(self, intensity=0.3) -> Filter:
        return self.create_quick_filter(FilterType.TWIRL, intensity)
    
    def apply_circular_grayscale(self, center_x, center_y, radius=100.0, intensity=1.0) -> Filter:
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
    
    def apply_rectangular_blur(self, x, y, width, height, intensity=0.5) -> Filter:
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
    
    def begin_frame(self):
        """Start rendering a new frame."""
        if not self._initialized:
            return
        if self.filters:
            glBindFramebuffer(GL_FRAMEBUFFER, self._filter_framebuffer)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    def end_frame(self):
        """Finish rendering and apply filters."""
        if not self._initialized:
            return
        if self.filters:
            self._apply_filters()
        pygame.display.flip()
    
    def _apply_filters(self):
        """Apply stacked filters to the screen."""
        if not self.filters or not self.filter_shader.program:
            return
        
        # Update filter animations
        for f in self.filters:
            if f.enabled:
                f.update(1.0/60.0)
        
        # Use filter shader
        self.filter_shader.use()
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._filter_texture)
        glUniform1i(self.filter_shader._get_uniform_location("screenTexture"), 0)
        glUniform2f(self.filter_shader._get_uniform_location("screenSize"), self.width, self.height)
        
        # Apply each filter (they stack)
        for f in self.filters:
            if not f.enabled:
                continue
            
            # Map filter type to int
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
        return pygame.display.get_surface()
    
    def set_surface(self, surface: Optional[pygame.Surface]):
        """Render to a custom surface using framebuffer."""
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
        """Convert a pygame Surface to an OpenGL texture."""
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
    
    def _surface_to_texture_cached(self, surface: pygame.Surface) -> int:
        """Cached version of surface-to-texture."""
        surf_id = id(surface)
        if surf_id in self._texture_cache:
            tex, size = self._texture_cache[surf_id]
            if size == surface.get_size():
                return tex
        tex = self._surface_to_texture(surface)
        self._texture_cache[surf_id] = (tex, surface.get_size())
        return tex
    
    def _convert_color(self, color: Tuple[int, int, int, float]) -> Tuple[float, float, float, float]:
        """Convert color tuple to normalized RGBA."""
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
    # Scissor Test
    # ========================================================================
    
    def enable_scissor(self, x: int, y: int, width: int, height: int):
        if not self._initialized:
            return
        x, y, width, height = int(x), int(y), abs(int(width)), abs(int(height))
        glEnable(GL_SCISSOR_TEST)
        gl_scissor_y = self.height - (y + height)
        gl_scissor_x = max(0, x)
        gl_scissor_y = max(0, gl_scissor_y)
        gl_scissor_width = abs(min(width, self.width - gl_scissor_x))
        gl_scissor_height = abs(min(height, self.height - gl_scissor_y))
        glScissor(gl_scissor_x, gl_scissor_y, gl_scissor_width, gl_scissor_height)
    
    def disable_scissor(self):
        if not self._initialized:
            return
        glDisable(GL_SCISSOR_TEST)
    
    # ========================================================================
    # Drawing Primitives
    # ========================================================================
    
    def draw_rect(self, x: int, y: int, width: int, height: int,
              color: tuple, fill: bool = True, anchor_point: tuple = (0.0, 0.0),
              border_width: int = 1, surface: Optional[pygame.Surface] = None,
              corner_radius: Union[int, Tuple[int, int, int, int]] = 0,
              border_color: Optional[Union[Color, Tuple[int, int, int, float]]] = None):
        """
        Draw a rectangle with optional border and fill.

        Args:
            color: Fill color (if fill=True)
            fill: If True, draw filled rectangle; if False, draw only outline
            border_width: Width of border in pixels (only used if fill=True and border_color given)
            border_color: Color of border (if None, uses color for border when fill=False)
        """
        if not self._initialized:
            return

        x = x - int(anchor_point[0] * width)
        y = y - int(anchor_point[1] * height)

        if surface:
            old = self._current_target
            self.set_surface(surface)

        # Normalize corner radii
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

        # If fill is False, just draw an outline using the provided color
        if not fill:
            self._draw_outline_rect(x, y, width, height, color, border_width, radii)
            if surface:
                self.set_surface(old)
            return

        # Fill mode: draw border first if border_color is given and border_width > 0
        if border_color is not None and border_width > 0:
            # Draw border rectangle (slightly larger)
            border_w = border_width * 2
            border_h = border_width * 2
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(x - border_width, y - border_width,
                                    width + border_w, height + border_h,
                                    border_color, fill=True, border_width=0)
            else:
                # For rounded corners, we need to expand the radii by border_width
                expanded_radii = tuple(r + border_width for r in radii)
                self._draw_rounded_rect(x - border_width, y - border_width,
                                        width + border_w, height + border_h,
                                        border_color, fill=True,
                                        border_width=0, radii=expanded_radii)
            # Then draw the inner filled rectangle
            inner_x = x + border_width
            inner_y = y + border_width
            inner_w = width - border_w
            inner_h = height - border_h
            if inner_w > 0 and inner_h > 0:
                if all(r == 0 for r in radii):
                    self._draw_sharp_rect(inner_x, inner_y, inner_w, inner_h,
                                        color, fill=True, border_width=0)
                else:
                    # Shrink radii accordingly
                    inner_radii = tuple(max(0, r - border_width) for r in radii)
                    self._draw_rounded_rect(inner_x, inner_y, inner_w, inner_h,
                                            color, fill=True, border_width=0,
                                            radii=inner_radii)
        else:
            # No border, just draw the filled rectangle
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(x, y, width, height, color, fill=True, border_width=0)
            else:
                self._draw_rounded_rect(x, y, width, height, color, fill=True,
                                        border_width=0, radii=radii)

        if surface:
            self.set_surface(old)

    def _draw_outline_rect(self, x, y, width, height, color, border_width, radii):
        """Draw only the outline (border) of a rectangle."""
        if all(r == 0 for r in radii):
            self._draw_sharp_rect(x, y, width, height, color, fill=False, border_width=border_width)
        else:
            self._draw_rounded_rect(x, y, width, height, color, fill=False,
                                    border_width=border_width, radii=radii)

    def _draw_sharp_rect(self, x, y, width, height, color, fill=True, border_width=1):
        """Draw a sharp rectangle (no rounded corners)."""
        self.simple_shader.use()
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"),
                    float(self.width), float(self.height))
        r, g, b, a = self._convert_color(color)

        if not fill:
            # Outline: draw a hollow rectangle
            # For outlines, we need to draw the border as a separate shape.
            # Use the same method as before: draw a slightly larger rect with no fill? Actually simpler:
            # We can draw the outline as four thin lines (not efficient) or use a shader.
            # Since we have a simple shader, we'll draw the outline by drawing the rect as a wireframe.
            # But for simplicity, we'll reuse the existing outline method: draw a filled rect
            # with border_width as the stroke? Actually the old method for outline wasn't correct.
            # Let's implement a proper thick outline using the same shader but with a different transform.
            # We draw the border as a filled rect that is larger by border_width, then subtract the inner.
            # But that's complex. Instead, we'll draw four rectangles for each side.
            # This is efficient enough for UI borders.
            # Top edge
            self._draw_sharp_rect(x, y, width, border_width, color, fill=True, border_width=0)
            # Bottom edge
            self._draw_sharp_rect(x, y + height - border_width, width, border_width, color, fill=True, border_width=0)
            # Left edge
            self._draw_sharp_rect(x, y + border_width, border_width, height - 2*border_width, color, fill=True, border_width=0)
            # Right edge
            self._draw_sharp_rect(x + width - border_width, y + border_width, border_width, height - 2*border_width, color, fill=True, border_width=0)
        else:
            # Filled rect
            glUniform4f(self.simple_shader._get_uniform_location("uTransform"),
                        float(x), float(y), float(width), float(height))
            glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)
            glBindVertexArray(self.simple_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)

        self.simple_shader.unuse()

    def _draw_rounded_rect(self, x, y, w, h, color, fill=True, border_width=1, radii=(0,0,0,0)):
        """Draw a rounded rectangle, optionally as an outline."""
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
    
    def draw_line(self, start_x, start_y, end_x, end_y, color, width=2, surface=None):
        if not self._initialized or not self.simple_shader.program:
            return
        if surface:
            old = self._current_target
            self.set_surface(surface)
        
        if start_x == end_x and start_y == end_y:
            return
        
        # Use thick line method
        self._draw_thick_line(start_x, start_y, end_x, end_y, color, width)
        
        if surface:
            self.set_surface(old)
    
    def _draw_thick_line(self, x1, y1, x2, y2, color, width):
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
    
    def draw_lines(self, points: List[Tuple[Tuple[int, int], Tuple[int, int]]], color: tuple, width: int = 2, surface=None):
        for (x1, y1), (x2, y2) in points:
            self.draw_line(x1, y1, x2, y2, color, width, surface)
    
    def draw_circle(self, center_x, center_y, radius, color, fill=True, border_width=1, surface=None, anchor_point=(0.5, 0.5)):
        if not self._initialized or not self.simple_shader.program:
            return
        
        if surface:
            old = self._current_target
            self.set_surface(surface)
        
        width = radius * 2
        height = radius * 2
        x = center_x - int(anchor_point[0] * width)
        y = center_y - int(anchor_point[1] * height)
        
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
    
    def _generate_filled_circle_geometry(self, segments):
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
    
    def _generate_hollow_circle_geometry(self, segments:int, border_width:float|int, radius:float|int):
        segments = int(segments) # make sure that it is an integer
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
    
    def _upload_geometry(self, vertices, indices):
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
    
    def draw_polygon(self, points, color, fill=True, border_width=1, surface=None, anchor_point=(0.0, 0.0)):
        if not self._initialized or len(points) < 3:
            return
        
        if surface:
            old = self._current_target
            self.set_surface(surface)
        
        # Adjust points by anchor
        points = [(x + anchor_point[0], y + anchor_point[1]) for x, y in points]
        
        # Generate geometry (simple triangulation – assumes convex)
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
    
    def _generate_filled_polygon_geometry(self, points):
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
    
    def _generate_hollow_polygon_geometry(self, points, border_width):
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
            # inner point toward center
            center_x = 0.5
            center_y = 0.5
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
    
    def draw_text(self, text: str, x: int, y: int, color, font, surface=None,
              anchor_point=(0.0, 0.0), flip=(False, False), rotate=0.0, *args, **kwargs):
        if not self._initialized:
            return

        # ========== CONVERT ANY COLOR TO VALID pygame.Color ==========
        try:
            if isinstance(color, pygame.Color):
                pygame_color = color
            elif isinstance(color, Color):  # your custom class
                pygame_color = pygame.Color(color.r, color.g, color.b, int(color.a * 255))
            elif isinstance(color, (tuple, list)):
                if len(color) >= 3:
                    # Ensure integer components
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
            print(f"Color conversion error: {e}, falling back to white")
            pygame_color = pygame.Color(255, 255, 255)

        # Normalize for shader
        r, g, b, a = pygame_color.r, pygame_color.g, pygame_color.b, pygame_color.a
        rgba = (r/255.0, g/255.0, b/255.0, a/255.0)

        # ========== FONT HANDLING ==========
        isBold = kwargs.get('bold', False)
        isItalic = kwargs.get('italic', False)
        if isinstance(font, tuple):
            font = pygame.font.SysFont(font[0], font[1], isBold, isItalic)

        # ========== CACHING (use RGB tuple as key) ==========
        cache_key = (text, font, (r, g, b))
        now = time.time()
        if cache_key in self._text_cache:
            tex, (tw, th) = self._text_cache[cache_key]
            self._text_cache_last_used[cache_key] = now
        else:
            # CRITICAL: use pygame_color, never a raw tuple
            text_surface = font.render(text, True, pygame_color)
            tex = self._surface_to_texture(text_surface)
            tw, th = text_surface.get_size()
            self._text_cache[cache_key] = (tex, (tw, th))
            self._text_cache_last_used[cache_key] = now

        # Cleanup old cache entries
        if now - self._last_text_cache_cleanup >= self._text_cache_cleanup_interval:
            self._cleanup_text_cache(now)

        # ========== POSITIONING ==========
        x = x - int(anchor_point[0] * tw)
        y = y - int(anchor_point[1] * th)

        old_target = None
        if surface:
            old_target = self._current_target
            self.set_surface(surface)

        # ========== FAST PATH (no flip/rotate) ==========
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
            # ========== SLOW PATH (flip/rotate) – same as your existing code ==========
            center_x = x + tw / 2.0
            center_y = y + th / 2.0

            w2 = tw / 2.0
            h2 = th / 2.0
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
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices_arr.itemsize, ctypes.c_void_p(2 * vertices_arr.itemsize))
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
   
    def _cleanup_text_cache(self, now: float):
        """Remove text cache entries that haven't been used for longer than timeout."""
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
    
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        self.blit(surface, (x, y))
    
    def blit(self, source: pygame.Surface, dest: Union[Tuple[int, int], pygame.Rect],
             area: Optional[pygame.Rect] = None, special_flags: int = 0):
        if not self._initialized or not self.texture_shader.program:
            return
        
        if isinstance(dest, pygame.Rect):
            x, y, w, h = dest
        else:
            x, y = dest
            w, h = source.get_size()
        
        if area:
            source = source.subsurface(area)
            w, h = area.width, area.height
        
        tex = self._surface_to_texture_cached(source)
        
        self.texture_shader.use()
        glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        glUniform4f(self.texture_shader._get_uniform_location("uTransform"), x, y, w, h)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex)
        glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
        
        if source.get_flags() & pygame.SRCALPHA:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_BLEND)
        
        glBindVertexArray(self.texture_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        self.texture_shader.unuse()
    
    def fill_screen(self, color: Tuple[int, int, int, float]):
        r, g, b, a = self._convert_color(color)
        glClearColor(r, g, b, a)
        glClear(GL_COLOR_BUFFER_BIT)
    
    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # ========================================================================
    # Particle Rendering
    # ========================================================================
    
    def render_particles(self, particle_data: Dict[str, Any], camera):
        """
        Render particles using instancing.
        particle_data should contain:
            - active_count: int
            - positions: np.ndarray (N,2) world positions
            - sizes: np.ndarray (N,) sizes in world units (will be zoomed by camera)
            - colors: np.ndarray (N,3) uint8 RGB
            - alphas: np.ndarray (N,) uint8 alpha
        """
        if not self._initialized or not self.particle_shader.program:
            return
        
        active = particle_data['active_count']
        if active == 0:
            return
        
        # Ensure buffers are large enough
        self._ensure_particle_capacity(active)
        
        # Convert world positions to screen positions
        world_pos = particle_data['positions']
        screen_pos = np.zeros((active, 2), dtype=np.float32)
        for i in range(active):
            sp = camera.world_to_screen(world_pos[i])
            screen_pos[i] = [sp.x, sp.y]
        
        # Convert sizes with camera zoom
        sizes = camera.convert_size_zoom_list(particle_data['sizes'][:active], 'ndarray')
        alphas = particle_data['alphas'][:active] / 255.0
        colors = particle_data['colors'][:active] / 255.0
        
        # Pack instance data: x, y, size, alpha
        instance_data = np.zeros((active, 4), dtype=np.float32)
        instance_data[:, 0] = screen_pos[:, 0]
        instance_data[:, 1] = screen_pos[:, 1]
        instance_data[:, 2] = np.maximum(2.0, sizes)  # minimum size 2
        instance_data[:, 3] = alphas
        
        # Color data: r, g, b, a (alpha always 1.0, we use instance alpha)
        color_data = np.zeros((active, 4), dtype=np.float32)
        color_data[:, 0:3] = colors
        color_data[:, 3] = 1.0
        
        # Upload instance data
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_data.nbytes, instance_data, GL_DYNAMIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, color_data.nbytes, color_data, GL_DYNAMIC_DRAW)
        
        # Draw
        self.particle_shader.use()
        glUniform2f(self.particle_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        
        glBindVertexArray(self.particle_shader.vao)
        glDrawArraysInstanced(GL_POINTS, 0, 1, active)
        glBindVertexArray(0)
        
        self.particle_shader.unuse()
    
    def _ensure_particle_capacity(self, required: int):
        """Dynamically resize instance buffers if needed."""
        if required <= self._max_particles:
            return
        # Calculate next power of two
        new_size = 1
        while new_size < required:
            new_size *= 2
        
        # Resize buffers
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        glBufferData(GL_ARRAY_BUFFER, new_size * 4 * 4, None, GL_DYNAMIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, new_size * 4 * 4, None, GL_DYNAMIC_DRAW)
        
        self._max_particles = new_size
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    def cleanup(self):
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
        
        # Delete texture cache
        for tex, _ in self._texture_cache.values():
            glDeleteTextures(1, [tex])
        
        self._circle_cache.clear()
        self._polygon_cache.clear()
        self._texture_cache.clear()
        self._text_cache.clear()
        
        self._initialized = False
        
    def set_blend_mode(self, mode: Literal['normal', 'add', 'multiply', 'screen']):
        """
        Set the OpenGL blend mode.
        mode can be 'normal', 'add', 'multiply', etc.
        """
        if mode == 'normal':
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        elif mode == 'add':
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        elif mode == 'multiply':
            glBlendFunc(GL_DST_COLOR, GL_ZERO)  # Multiplies destination by source color
        elif mode == 'screen':
            glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR)
        else:
            print(f"Unknown blend mode: {mode}")