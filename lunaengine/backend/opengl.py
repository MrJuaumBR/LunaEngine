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

Shader files are now loaded from lunaengine/assets/shaders/ by default.
Users can add custom shader search paths via set_shader_folder().
"""

from __future__ import annotations

import ctypes
import math
import os
import sys
import time
import weakref
from collections import OrderedDict
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

import numpy as np
import pygame

from ..ui.themes import ThemeStyle, UiShadow
from ..utils import math_utils as math_utils
from .types import Color, ColorKeys

# ---------------------------------------------------------------------
# OpenGL imports – explicit namespaced to avoid Pylance warnings
# ---------------------------------------------------------------------
try:
    import OpenGL.GL as gl
    from OpenGL.GL.shaders import compileProgram, compileShader

    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("OpenGL not available - falling back to software rendering")


# ---------------------------------------------------------------------
# Shader folder management
# ---------------------------------------------------------------------
_DEFAULT_SHADER_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "shaders",
)

_shader_folder = _DEFAULT_SHADER_FOLDER


def set_shader_folder(folder: str) -> None:
    global _shader_folder
    _shader_folder = os.path.abspath(folder)


def get_shader_folder() -> str:
    return _shader_folder


# ---------------------------------------------------------------------
# Filter Enums and Classes
# ---------------------------------------------------------------------
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
    def __init__(
        self,
        filter_type: FilterType = FilterType.NONE,
        intensity: float = 1.0,
        region_type: FilterRegionType = FilterRegionType.FULLSCREEN,
        region_pos: Tuple[float, float] = (0, 0),
        region_size: Tuple[float, float] = (100, 100),
        radius: float = 50.0,
        feather: float = 10.0,
        blend_mode: str = "normal",
    ):
        self.filter_type = filter_type
        self.intensity = max(0.0, min(1.0, intensity))
        self.region_type = region_type
        self.region_pos = region_pos
        self.region_size = region_size
        self.radius = max(1.0, radius)
        self.feather = max(0.0, feather)
        self.blend_mode = blend_mode
        self.enabled = True
        self.time = 0.0

    def update(self, dt: float) -> None:
        self.time += dt

    def copy(self) -> Filter:
        return Filter(
            self.filter_type,
            self.intensity,
            self.region_type,
            self.region_pos,
            self.region_size,
            self.radius,
            self.feather,
            self.blend_mode,
        )


# ---------------------------------------------------------------------
# Base Shader Program
# ---------------------------------------------------------------------
class ShaderProgram:
    def __init__(self, shader_name: str, has_geometry: bool = False):
        self.shader_name = shader_name
        self.has_geometry = has_geometry

        self.vertex_source = self._load_source("vert")
        self.fragment_source = self._load_source("frag")
        self.geometry_source = self._load_source("geom") if has_geometry else None

        self.program = None
        self.vao = self.vbo = self.ebo = None
        self._uniform_locations: Dict[str, int] = {}

        if self.vertex_source and self.fragment_source:
            self._create_program(
                self.vertex_source, self.fragment_source, self.geometry_source
            )
            if self.program:
                self._setup_geometry()

    def _load_source(self, stage: str) -> Optional[str]:
        dedicated_path = os.path.join(
            get_shader_folder(), f"{self.shader_name}.{stage}"
        )
        if os.path.exists(dedicated_path):
            with open(dedicated_path, "r") as f:
                return f.read()

        combined_path = os.path.join(get_shader_folder(), f"shaders.{stage}")
        if os.path.exists(combined_path):
            with open(combined_path, "r") as f:
                content = f.read()
            lines = content.splitlines(keepends=False)
            version_line_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("#version"):
                    version_line_idx = i
                    break

            if version_line_idx != -1:
                define_line = f"#define LUNA_SHADER_{self.shader_name.upper()}"
                lines.insert(version_line_idx + 1, define_line)
            else:
                print(
                    f"Warning: No #version found in {combined_path}, prepending default."
                )
                lines = [
                    f"#version 330 core",
                    f"#define LUNA_SHADER_{self.shader_name.upper()}",
                ] + lines
            return "\n".join(lines)
        return None

    def _get_uniform_location(self, name: str) -> int:
        if name not in self._uniform_locations:
            self._uniform_locations[name] = gl.glGetUniformLocation(self.program, name)
        return self._uniform_locations[name]

    def _create_program(
        self,
        vertex_source: str,
        fragment_source: str,
        geometry_source: Optional[str] = None,
    ) -> None:
        try:
            vertex = compileShader(vertex_source, gl.GL_VERTEX_SHADER)
            fragment = compileShader(fragment_source, gl.GL_FRAGMENT_SHADER)
            shaders = [vertex, fragment]
            if geometry_source:
                geometry = compileShader(geometry_source, gl.GL_GEOMETRY_SHADER)
                shaders.append(geometry)
            self.program = compileProgram(*shaders)
        except Exception as e:
            print(f"Shader compilation failed for '{self.shader_name}': {e}")
            self.program = None

    def use(self) -> None:
        if self.program:
            gl.glUseProgram(self.program)

    def unuse(self) -> None:
        gl.glUseProgram(0)

    def _setup_geometry(self) -> None:
        pass


# ---------------------------------------------------------------------
# Specific Shader Implementations
# ---------------------------------------------------------------------
class ParticleShader(ShaderProgram):
    def __init__(self):
        super().__init__("particle")

    def _setup_geometry(self) -> None:
        vertices = np.array([0.0, 0.0], dtype=np.float32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.instance_data_vbo = gl.glGenBuffers(1)
        self.instance_color_vbo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.instance_data_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, 1024 * 4 * 4, None, gl.GL_DYNAMIC_DRAW)
        gl.glVertexAttribPointer(
            1, 4, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribDivisor(1, 1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.instance_color_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, 1024 * 4 * 4, None, gl.GL_DYNAMIC_DRAW)
        gl.glVertexAttribPointer(
            2, 4, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribDivisor(2, 1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)


class SimpleShader(ShaderProgram):
    def __init__(self):
        super().__init__("simple")

    def _setup_geometry(self) -> None:
        vertices = np.array([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0], dtype=np.float32)
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)


class TextureShader(ShaderProgram):
    def __init__(self):
        super().__init__("texture")

    def _setup_geometry(self) -> None:
        vertices = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                1.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                1.0,
                0.0,
                1.0,
            ],
            dtype=np.float32,
        )
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )

        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(
            1,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            4 * vertices.itemsize,
            ctypes.c_void_p(2 * vertices.itemsize),
        )
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

class RoundedRectShader(ShaderProgram):
    def __init__(self):
        super().__init__("rounded_rect")

    def _setup_geometry(self) -> None:
        vertices = np.array([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0], dtype=np.float32)
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)


class FilterShader(ShaderProgram):
    def __init__(self):
        super().__init__("filter")

    def _setup_geometry(self) -> None:
        # UVs: top-left (0,0), bottom-left (0,1), bottom-right (1,1), top-right (1,0)
        vertices = np.array(
            [
                -1.0,
                1.0,
                0.0,
                0.0,
                -1.0,
                -1.0,
                0.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
            ],
            dtype=np.float32,
        )
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(
            1,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            4 * vertices.itemsize,
            ctypes.c_void_p(2 * vertices.itemsize),
        )
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

class MaskShader(ShaderProgram):
    def __init__(self):
        super().__init__("mask")

    def _setup_geometry(self) -> None:
        # UVs: top-left (0,0), bottom-left (0,1), bottom-right (1,1), top-right (1,0)
        vertices = np.array(
            [
                -1.0,
                1.0,
                0.0,
                0.0,
                -1.0,
                -1.0,
                0.0,
                1.0,
                1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
            ],
            dtype=np.float32,
        )
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(
            1,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            4 * vertices.itemsize,
            ctypes.c_void_p(2 * vertices.itemsize),
        )
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

class DepthShader(ShaderProgram):
    def __init__(self):
        super().__init__("depth", has_geometry=True)

    def _setup_geometry(self) -> None:
        vertices = np.array([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0], dtype=np.float32)
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self.ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)

# ---------------------------------------------------------------------
# Main OpenGLRenderer
# ---------------------------------------------------------------------
class OpenGLRenderer:
    camera_position = pygame.math.Vector2(0, 0)

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._initialized = False

        self.simple_shader = None
        self.texture_shader = None
        self.particle_shader = None
        self.filter_shader = None
        self.rounded_rect_shader = None
        self.mask_shader = None

        self._max_particles = 1024
        self.on_max_particles_change = []

        self.filters = []
        self._filter_framebuffer = None
        self._filter_texture = None
        self._filter_renderbuffer = None

        self._circle_cache = {}
        self._polygon_cache = {}
        self._gradient_cache: Dict[Tuple, int] = OrderedDict()
        self._gradient_cache_max_size = 64

        self._current_target = None

        self._texture_cache = weakref.WeakKeyDictionary()
        self._text_cache = {}
        self._text_cache_last_used = {}
        self._text_cache_timeout = 10.0
        self._texture_cache_timeout = 10.0
        self._last_texture_cache_cleanup = 0.0
        self._last_text_cache_cleanup = 0.0
        self._text_cache_cleanup_interval = 5.0

        self._scissor_stack = []

        # Temporary FBOs for gradient/mask composition
        self._temp = {
            "fbo_mask": None,
            "fbo_composite": None,
            "tex_mask": None,
            "tex_composite": None,
            "rb_mask": None,
            "rb_composite": None,
            "width": 0,
            "height": 0,
        }

    def get_opengl_version(self) -> str:
        return gl.glGetString(gl.GL_VERSION).decode("ascii")

    def set_text_cache_timeout(self, seconds: float) -> None:
        self._text_cache_timeout = max(0.1, seconds)

    def get_cache_usage(self, target: str = "all", humanize: bool = False):
        if target == "all":
            return {
                "text": (
                    math_utils.humanize_size(sys.getsizeof(self._text_cache))
                    if humanize
                    else sys.getsizeof(self._text_cache)
                ),
                "texture": (
                    math_utils.humanize_size(sys.getsizeof(self._texture_cache))
                    if humanize
                    else sys.getsizeof(self._texture_cache)
                ),
                "circle": (
                    math_utils.humanize_size(sys.getsizeof(self._circle_cache))
                    if humanize
                    else sys.getsizeof(self._circle_cache)
                ),
                "polygon": (
                    math_utils.humanize_size(sys.getsizeof(self._polygon_cache))
                    if humanize
                    else sys.getsizeof(self._polygon_cache)
                ),
                "total": self.get_cache_usage("total", humanize),
            }
        elif target == "text":
            val = sys.getsizeof(self._text_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == "texture":
            val = sys.getsizeof(self._texture_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == "circle":
            val = sys.getsizeof(self._circle_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == "polygon":
            val = sys.getsizeof(self._polygon_cache)
            return math_utils.humanize_size(val) if humanize else val
        elif target == "total":
            total = (
                sys.getsizeof(self._text_cache)
                + sys.getsizeof(self._texture_cache)
                + sys.getsizeof(self._circle_cache)
                + sys.getsizeof(self._polygon_cache)
            )
            return math_utils.humanize_size(total) if humanize else total
        else:
            raise ValueError(f"Invalid cache target: {target}")

    @property
    def max_particles(self) -> int:
        return self._max_particles

    @max_particles.setter
    def max_particles(self, value: int) -> None:
        if value > self._max_particles:
            for callback in self.on_max_particles_change:
                callback(value)
        self._max_particles = value

    def initialize(self) -> bool:
        if not OPENGL_AVAILABLE:
            return False
        print(f"Initializing OpenGL renderer for {self.width}x{self.height}...")
        print(f"Shader folder: {get_shader_folder()}")

        gl.glDisable(gl.GL_FRAMEBUFFER_SRGB)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glClearColor(0.1, 0.1, 0.3, 1.0)
        gl.glEnable(gl.GL_PROGRAM_POINT_SIZE)

        self.simple_shader = SimpleShader()
        self.texture_shader = TextureShader()
        self.particle_shader = ParticleShader()
        self.filter_shader = FilterShader()
        self.rounded_rect_shader = RoundedRectShader()
        self.mask_shader = MaskShader()
        
        if not all(
            [
                self.simple_shader.program,
                self.texture_shader.program,
                self.particle_shader.program,
                self.filter_shader.program,
                self.rounded_rect_shader.program,
                self.mask_shader.program,
            ]
        ):
            print("Shader initialization failed")
            return False

        self._initialize_filter_framebuffer()
        self._initialized = True
        print("OpenGL renderer initialized successfully")
        return True

    def _initialize_filter_framebuffer(self) -> bool:
        try:
            self._filter_framebuffer = gl.glGenFramebuffers(1)
            self._filter_texture = gl.glGenTextures(1)
            self._filter_renderbuffer = gl.glGenRenderbuffers(1)

            gl.glBindTexture(gl.GL_TEXTURE_2D, self._filter_texture)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D,
                0,
                gl.GL_RGBA,
                self.width,
                self.height,
                0,
                gl.GL_RGBA,
                gl.GL_UNSIGNED_BYTE,
                None,
            )
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE
            )
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE
            )

            gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, self._filter_renderbuffer)
            gl.glRenderbufferStorage(
                gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, self.width, self.height
            )

            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._filter_framebuffer)
            gl.glFramebufferTexture2D(
                gl.GL_FRAMEBUFFER,
                gl.GL_COLOR_ATTACHMENT0,
                gl.GL_TEXTURE_2D,
                self._filter_texture,
                0,
            )
            gl.glFramebufferRenderbuffer(
                gl.GL_FRAMEBUFFER,
                gl.GL_DEPTH_STENCIL_ATTACHMENT,
                gl.GL_RENDERBUFFER,
                self._filter_renderbuffer,
            )

            if (
                gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER)
                != gl.GL_FRAMEBUFFER_COMPLETE
            ):
                print("Filter framebuffer is not complete!")
                return False

            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            return True
        except Exception as e:
            print(f"Failed to initialize filter framebuffer: {e}")
            return False

    # ---------------------------------------------------------------------
    # Filter System
    # ---------------------------------------------------------------------
    def add_filter(self, filter_obj: Filter) -> None:
        
        self.filters.append(filter_obj)

    def remove_filter(self, filter_obj: Filter) -> None:
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)

    def clear_filters(self) -> None:
        self.filters.clear()

    def create_quick_filter(
        self,
        filter_type: FilterType,
        intensity: float = 1.0,
        x: float = 0,
        y: float = 0,
        width: float = None,
        height: float = None,
        radius: float = 50.0,
        feather: float = 10.0,
    ) -> Filter:
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
            feather=feather,
        )
        self.add_filter(filter_obj)
        return filter_obj

    def apply_vignette(self, intensity: float = 0.7, feather: float = 100.0) -> Filter:
        return self.create_quick_filter(FilterType.VIGNETTE, intensity, feather=feather)

    def apply_blur(
        self,
        intensity: float = 0.5,
        x: float = 0,
        y: float = 0,
        width: float = None,
        height: float = None,
    ) -> Filter:
        return self.create_quick_filter(
            FilterType.BLUR, intensity, x, y, width, height, feather=20.0
        )

    def apply_sepia(self, intensity: float = 1.0) -> Filter:
        return self.create_quick_filter(FilterType.SEPIA, intensity)

    def apply_grayscale(self, intensity: float = 1.0) -> Filter:
        return self.create_quick_filter(FilterType.GRAYSCALE, intensity)

    def apply_invert(self, intensity: float = 1.0) -> Filter:
        return self.create_quick_filter(FilterType.INVERT, intensity)

    def apply_warm_temperature(self, intensity: float = 0.5) -> Filter:
        return self.create_quick_filter(FilterType.TEMPERATURE_WARM, intensity)

    def apply_cold_temperature(self, intensity: float = 0.5) -> Filter:
        return self.create_quick_filter(FilterType.TEMPERATURE_COLD, intensity)

    def apply_night_vision(self, intensity: float = 0.9) -> Filter:
        return self.create_quick_filter(FilterType.NIGHT_VISION, intensity)

    def apply_crt_effect(self, intensity: float = 0.8) -> Filter:
        return self.create_quick_filter(FilterType.CRT, intensity)

    def apply_pixelate(self, intensity: float = 0.7) -> Filter:
        return self.create_quick_filter(FilterType.PIXELATE, intensity)

    def apply_bloom(self, intensity: float = 0.5) -> Filter:
        return self.create_quick_filter(FilterType.BLOOM, intensity)

    def apply_edge_detect(self, intensity: float = 0.8) -> Filter:
        return self.create_quick_filter(FilterType.EDGE_DETECT, intensity)

    def apply_emboss(self, intensity: float = 0.7) -> Filter:
        return self.create_quick_filter(FilterType.EMBOSS, intensity)

    def apply_sharpen(self, intensity: float = 0.5) -> Filter:
        return self.create_quick_filter(FilterType.SHARPEN, intensity)

    def apply_posterize(self, intensity: float = 0.6) -> Filter:
        return self.create_quick_filter(FilterType.POSTERIZE, intensity)

    def apply_neon(self, intensity: float = 0.7) -> Filter:
        return self.create_quick_filter(FilterType.NEON, intensity)

    def apply_radial_blur(self, intensity: float = 0.5) -> Filter:
        return self.create_quick_filter(FilterType.RADIAL_BLUR, intensity)

    def apply_fisheye(self, intensity: float = 0.4) -> Filter:
        return self.create_quick_filter(FilterType.FISHEYE, intensity)

    def apply_twirl(self, intensity: float = 0.3) -> Filter:
        return self.create_quick_filter(FilterType.TWIRL, intensity)

    def apply_circular_grayscale(
        self,
        center_x: float,
        center_y: float,
        radius: float = 100.0,
        intensity: float = 1.0,
    ) -> Filter:
        diameter = radius * 2
        filter_obj = Filter(
            filter_type=FilterType.GRAYSCALE,
            intensity=intensity,
            region_type=FilterRegionType.CIRCLE,
            region_pos=(center_x - radius, center_y - radius),
            region_size=(diameter, diameter),
            radius=1.0,
            feather=20.0,
        )
        self.add_filter(filter_obj)
        return filter_obj

    def apply_rectangular_blur(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        intensity: float = 0.5,
    ) -> Filter:
        filter_obj = Filter(
            filter_type=FilterType.BLUR,
            intensity=intensity,
            region_type=FilterRegionType.RECTANGLE,
            region_pos=(x, y),
            region_size=(width, height),
            radius=1.0,
            feather=15.0,
        )
        self.add_filter(filter_obj)
        return filter_obj

    # ---------------------------------------------------------------------
    # Frame Control
    # ---------------------------------------------------------------------
    def begin_frame(self) -> None:
        if not self._initialized:
            return
        if self.filters:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._filter_framebuffer)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    def end_frame(self) -> None:
        if not self._initialized:
            return
        if self.filters:
            self._apply_filters()
        pygame.display.flip()

    def apply_filter_to_texture(self, tex_id: int, width: int, height: int,
                                filter_type: FilterType, intensity: float = 1.0) -> int:
        """
        Render the texture through the filter shader and produce a new filtered texture.

        Args:
            tex_id: OpenGL texture ID of the source image.
            width, height: Dimensions of the texture (must match the texture).
            filter_type: The filter to apply (e.g., FilterType.BLUR).
            intensity: Filter intensity (0.0–1.0).

        Returns:
            int: New texture ID with the filter applied. Caller must delete it when done.
        """
        if not self._initialized or not self.filter_shader.program:
            return tex_id

        # Create a temporary FBO for the filtered result
        fbo = gl.glGenFramebuffers(1)
        filtered_tex = gl.glGenTextures(1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, filtered_tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                gl.GL_TEXTURE_2D, filtered_tex, 0)
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            gl.glDeleteFramebuffers(1, [fbo])
            gl.glDeleteTextures(1, [filtered_tex])
            return tex_id

        # Save current viewport
        old_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        gl.glViewport(0, 0, width, height)

        # Clear and draw the source texture with the filter shader
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.filter_shader.use()
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex_id)
        gl.glUniform1i(self.filter_shader._get_uniform_location("screenTexture"), 0)
        gl.glUniform2f(self.filter_shader._get_uniform_location("screenSize"), width, height)

        # Map FilterType to integer (same as in _apply_filters)
        filter_type_map = {
            FilterType.NONE: 0,
            FilterType.BLUR: 2,
            # ... add other types as needed
        }
        gl.glUniform1i(self.filter_shader._get_uniform_location("filterType"),
                    filter_type_map.get(filter_type, 0))
        gl.glUniform1f(self.filter_shader._get_uniform_location("intensity"), intensity)
        gl.glUniform1f(self.filter_shader._get_uniform_location("time"), 0.0)
        # Fullscreen region
        gl.glUniform1i(self.filter_shader._get_uniform_location("regionType"), 0)
        gl.glUniform4f(self.filter_shader._get_uniform_location("regionParams"), 0, 0, 0, 0)
        gl.glUniform1f(self.filter_shader._get_uniform_location("radius"), 1.0)
        gl.glUniform1f(self.filter_shader._get_uniform_location("feather"), 0.0)

        gl.glBindVertexArray(self.filter_shader.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        self.filter_shader.unuse()

        # Restore viewport and framebuffer
        gl.glViewport(old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3])
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glDeleteFramebuffers(1, [fbo])

        return filtered_tex
    
    def _apply_filters(self) -> None:
        if not self.filters or not self.filter_shader.program:
            return
        for f in self.filters:
            if f.enabled:
                f.update(1.0 / 60.0)

        self.filter_shader.use()
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._filter_texture)
        gl.glUniform1i(self.filter_shader._get_uniform_location("screenTexture"), 0)
        gl.glUniform2f(
            self.filter_shader._get_uniform_location("screenSize"),
            self.width,
            self.height,
        )

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
        region_type_map = {
            FilterRegionType.FULLSCREEN: 0,
            FilterRegionType.RECTANGLE: 1,
            FilterRegionType.CIRCLE: 2,
        }

        for f in self.filters:
            if not f.enabled:
                continue
            filter_id = filter_type_map.get(f.filter_type, 0)
            gl.glUniform1i(
                self.filter_shader._get_uniform_location("filterType"), filter_id
            )
            gl.glUniform1f(
                self.filter_shader._get_uniform_location("intensity"), f.intensity
            )
            gl.glUniform1f(self.filter_shader._get_uniform_location("time"), f.time)
            gl.glUniform1i(
                self.filter_shader._get_uniform_location("regionType"),
                region_type_map.get(f.region_type, 0),
            )
            gl.glUniform4f(
                self.filter_shader._get_uniform_location("regionParams"),
                f.region_pos[0],
                f.region_pos[1],
                f.region_size[0],
                f.region_size[1],
            )
            gl.glUniform1f(self.filter_shader._get_uniform_location("radius"), f.radius)
            gl.glUniform1f(
                self.filter_shader._get_uniform_location("feather"), f.feather
            )
            gl.glBindVertexArray(self.filter_shader.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)

        gl.glBindVertexArray(0)
        self.filter_shader.unuse()
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    # ---------------------------------------------------------------------
    # Surface and Texture Management
    # ---------------------------------------------------------------------
    def get_surface(self) -> pygame.Surface:
        return pygame.display.get_surface()

    def set_surface(self, surface: Optional[pygame.Surface]) -> None:
        if surface == self._current_target:
            return
        if surface is None:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            self.width, self.height = self.get_surface().get_size()
        else:
            tex_id = self._surface_to_texture(surface)
            fbo = gl.glGenFramebuffers(1)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
            gl.glFramebufferTexture2D(
                gl.GL_FRAMEBUFFER,
                gl.GL_COLOR_ATTACHMENT0,
                gl.GL_TEXTURE_2D,
                tex_id,
                0,
            )
            if (
                gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER)
                != gl.GL_FRAMEBUFFER_COMPLETE
            ):
                print("Framebuffer not complete!")
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
                return
            self.width, self.height = surface.get_size()
        self._current_target = surface

    def capture_to_surface(self, draw_callback: Callable[[], None]) -> pygame.Surface:
        """Render once into an off-screen framebuffer and return a pygame surface.

        OpenGL rendering cannot populate a ``pygame.Surface`` directly. The old
        transition prototype attached a texture to an FBO but then read the
        untouched pygame surface, which produced blank captures. This helper
        owns the FBO, reads its pixels back, and restores the caller's target.
        """
        if not self._initialized:
            raise RuntimeError("Renderer must be initialized before capturing")

        old_target = self._current_target
        old_width, old_height = self.width, self.height
        old_fbo = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)
        old_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        width, height = old_width, old_height
        fbo = gl.glGenFramebuffers(1)
        tex = gl.glGenTextures(1)
        try:
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0,
                            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
            gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
                                      gl.GL_TEXTURE_2D, tex, 0)
            if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
                raise RuntimeError("Transition capture framebuffer is incomplete")

            self._current_target = None
            gl.glViewport(0, 0, width, height)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            draw_callback()
            pixels = gl.glReadPixels(0, 0, width, height, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
            return pygame.image.fromstring(pixels, (width, height), "RGBA", True).convert_alpha()
        finally:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, old_fbo)
            gl.glViewport(old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3])
            gl.glDeleteFramebuffers(1, [fbo])
            gl.glDeleteTextures(1, [tex])
            self.width, self.height = old_width, old_height
            self._current_target = old_target

    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        if surface.get_bytesize() != 4 or not (surface.get_flags() & pygame.SRCALPHA):
            converted = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
            converted.blit(surface, (0, 0))
            surface = converted
        w, h = surface.get_size()
        data = pygame.image.tostring(surface, "RGBA", False)
        tex = gl.glGenTextures(1)
        if tex == 0:
            return 0
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            w,
            h,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            data,
        )
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
        return tex

    def _surface_to_texture_cached(
        self,
        surface: pygame.Surface,
        rect: Optional[pygame.Rect] = None,
        dest: Optional[pygame.Rect] = None,
        flags: int = 0,
    ) -> int:
        rect_data = None
        if rect is not None:
            if isinstance(rect, pygame.Rect):
                rect_data = (rect.x, rect.y, rect.w, rect.h)
            else:
                rect_data = tuple(rect)
        dest_data = None
        if dest is not None:
            if isinstance(dest, pygame.Rect):
                dest_data = (dest.x, dest.y, dest.w, dest.h)
            else:
                dest_data = tuple(dest)
        sub_key = (rect_data, dest_data, flags)
        surf_cache = self._texture_cache.get(surface)
        if surf_cache is None:
            surf_cache = {}
            self._texture_cache[surface] = surf_cache
        if sub_key in surf_cache:
            tex, size, last_use = surf_cache[sub_key]
            if size == surface.get_size():
                return tex
        tex = self._surface_to_texture(surface)
        surf_cache[sub_key] = (tex, surface.get_size(), time.time())
        return tex

    def _convert_color(self, color):
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

    def _read_texture_pixel(
        self, tex_id: int, x: int = 0, y: int = 0
    ) -> Tuple[int, int, int, int]:
        if tex_id == 0 or not gl.glIsTexture(tex_id):
            return (0, 0, 0, 0)
        fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, fbo)
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D,
            tex_id,
            0,
        )
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            gl.glDeleteFramebuffers(1, [fbo])
            return (0, 0, 0, 0)
        data = gl.glReadPixels(x, y, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glDeleteFramebuffers(1, [fbo])
        return (data[0], data[1], data[2], data[3])

    # ---------------------------------------------------------------------
    # Scissor
    # ---------------------------------------------------------------------
    def enable_scissor(self, x, y, width, height):
        if not self._initialized:
            return
        x, y, width, height = int(x), int(y), abs(int(width)), abs(int(height))
        gl_y = self.height - (y + height)
        rect = (x, gl_y, width, height)
        if self._scissor_stack:
            prev = self._scissor_stack[-1]
            ix = max(prev[0], rect[0])
            iy = max(prev[1], rect[1])
            iw = min(prev[0] + prev[2], rect[0] + rect[2]) - ix
            ih = min(prev[1] + prev[3], rect[1] + rect[3]) - iy
            if iw <= 0 or ih <= 0:
                gl.glEnable(gl.GL_SCISSOR_TEST)
                gl.glScissor(0, 0, 0, 0)
                self._scissor_stack.append((ix, iy, iw, ih))
                return
            rect = (ix, iy, iw, ih)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(rect[0], rect[1], rect[2], rect[3])
        self._scissor_stack.append(rect)

    def disable_scissor(self):
        if not self._initialized or not self._scissor_stack:
            return
        self._scissor_stack.pop()
        if self._scissor_stack:
            prev = self._scissor_stack[-1]
            if prev[2] <= 0 or prev[3] <= 0:
                gl.glEnable(gl.GL_SCISSOR_TEST)
                gl.glScissor(prev[0], prev[1], prev[2], prev[3])
            else:
                gl.glEnable(gl.GL_SCISSOR_TEST)
                gl.glScissor(prev[0], prev[1], prev[2], prev[3])
        else:
            gl.glDisable(gl.GL_SCISSOR_TEST)

    # ---------------------------------------------------------------------
    # Drawing: Rectangles
    # ---------------------------------------------------------------------
    def draw_rect(
        self,
        x: Union[int, float],
        y: Union[int, float],
        width: Union[int, float],
        height : Union[int, float],
        color=None,
        fill=True,
        pivot=(0.0, 0.0),
        border_width: Union[int, float] = 1,
        surface=None,
        corner_radius: Union[int, float, Tuple[int|float, int|float, int|float, int|float]] = 0,
        border_color=None,
        style: Optional[Dict[str, Any]] = None,
    ):
        if not self._initialized:
            return
        x = x - int(pivot[0] * width)
        y = y - int(pivot[1] * height)
        if surface:
            old_target = self._current_target
            self.set_surface(surface)

        final_style = style.copy() if style else {}
        if border_color is not None:
            final_style["border_color"] = border_color
        if border_width != 1:
            final_style["border_width"] = border_width
        if color is not None and "gradient" not in final_style:
            final_style["solid_color"] = color

        # Shadow handling
        shadow_obj = final_style.get("shadow")
        if shadow_obj is not None:
            if isinstance(shadow_obj, UiShadow):
                shadow = {
                    "color": shadow_obj.color,
                    "alpha": shadow_obj.alpha,
                    "distance": shadow_obj.distance,
                    "direction": shadow_obj.direction,
                }
            elif isinstance(shadow_obj, dict):
                shadow = shadow_obj
            else:
                shadow = None

            if shadow is not None:
                distance = shadow.get("distance", 0.0)
                alpha = shadow.get("alpha", 0.0)
                if distance > 0 and alpha > 0:
                    direction = shadow.get("direction", (0.0, 0.0, 0.0, 0.0))
                    dx = (direction[2] - direction[0]) * distance
                    dy = (direction[3] - direction[1]) * distance
                    shadow_color = shadow.get("color", (0, 0, 0))
                    color_with_alpha = (*shadow_color, int(alpha * 255))
                    self._draw_rect_fast(
                        x + dx,
                        y + dy,
                        width,
                        height,
                        color=color_with_alpha,
                        fill=True,
                        border_width=0,
                        corner_radius=corner_radius,
                        border_color=None,
                    )
            final_style.pop("shadow", None)

        need_style = (
            final_style.get("gradient") is not None
            or final_style.get("blur", 0.0) > 0.0
        )

        if not need_style:
            self._draw_rect_fast(
                x,
                y,
                width,
                height,
                color,
                fill,
                border_width,
                corner_radius,
                border_color,
            )
            if surface:
                self.set_surface(old_target)
            return

        w, h = int(width), int(height)
        self._ensure_temp_fbo(w, h)
        old_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        gl.glViewport(0, 0, w, h)
        old_w, old_h = self.width, self.height
        self.width, self.height = w, h

        # Render mask
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_mask"])
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self._draw_rect_fast(
            0,
            0,
            w,
            h,
            (255, 255, 255, 255),
            fill=True,
            border_width=0,
            corner_radius=corner_radius,
            border_color=None,
        )

        # Generate fill texture
        if "gradient" in final_style:
            grad = final_style["gradient"]
            fill_tex = self._generate_gradient_texture(
                grad,
                w,
                h,
                final_style.get("gradient_type", "linear"),
                final_style.get("gradient_angle", 0.0),
            )
        else:
            solid = final_style.get("solid_color", (255, 255, 255, 255))
            r, g, b, a = self._convert_color(solid)
            surf = pygame.Surface((w, h), pygame.SRCALPHA, 32)
            surf.fill((int(r * 255), int(g * 255), int(b * 255), int(a * 255)))
            fill_tex = self._surface_to_texture(surf)

        if fill_tex == 0 or not gl.glIsTexture(fill_tex):
            self._draw_rect_fast(
                x,
                y,
                width,
                height,
                final_style.get("solid_color", (255, 255, 255, 255)),
                fill=True,
                border_width=0,
                corner_radius=corner_radius,
                border_color=None,
            )
            if final_style.get("border_width", 0) > 0 and final_style.get(
                "border_color"
            ):
                self._draw_rect_fast(
                    x,
                    y,
                    width,
                    height,
                    final_style["border_color"],
                    fill=False,
                    border_width=final_style["border_width"],
                    corner_radius=corner_radius,
                    border_color=None,
                )
            self.width, self.height = old_w, old_h
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            gl.glViewport(
                old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3]
            )
            if surface:
                self.set_surface(old_target)
            return

        # Composite
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_composite"])
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        self.mask_shader.use()
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, fill_tex)
        gl.glUniform1i(self.mask_shader._get_uniform_location("fillTexture"), 0)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._temp["tex_mask"])
        gl.glUniform1i(self.mask_shader._get_uniform_location("maskTexture"), 1)
        gl.glBindVertexArray(self.mask_shader.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        self.mask_shader.unuse()

        if final_style.get("border_width", 0) > 0 and final_style.get("border_color"):
            self._draw_rect_fast(
                0,
                0,
                w,
                h,
                final_style["border_color"],
                fill=False,
                border_width=final_style["border_width"],
                corner_radius=corner_radius,
                border_color=None,
            )

        self.width, self.height = old_w, old_h
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(
            old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3]
        )

        self.texture_shader.use()
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._temp["tex_composite"])
        gl.glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
        gl.glUniform2f(
            self.texture_shader._get_uniform_location("uScreenSize"),
            self.width,
            self.height,
        )
        gl.glUniform4f(
            self.texture_shader._get_uniform_location("uTransform"), x, y, w, h
        )
        gl.glBindVertexArray(self.texture_shader.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        self.texture_shader.unuse()

        if surface:
            self.set_surface(old_target)

    def _draw_rect_fast(
        self,
        x,
        y,
        width,
        height,
        color,
        fill=True,
        border_width=1,
        corner_radius=0,
        border_color=None,
    ):
        if isinstance(corner_radius, (int, float)) and corner_radius > 0:
            radii = (corner_radius, corner_radius, corner_radius, corner_radius)
        elif isinstance(corner_radius, (tuple, list)) and any(
            r > 0 for r in corner_radius
        ):
            if len(corner_radius) == 1:
                radii = (
                    corner_radius[0],
                    corner_radius[0],
                    corner_radius[0],
                    corner_radius[0],
                )
            elif len(corner_radius) == 2:
                radii = (
                    corner_radius[0],
                    corner_radius[1],
                    corner_radius[0],
                    corner_radius[1],
                )
            elif len(corner_radius) == 3:
                radii = (
                    corner_radius[0],
                    corner_radius[1],
                    corner_radius[2],
                    corner_radius[1],
                )
            else:
                radii = (
                    corner_radius[0],
                    corner_radius[1],
                    corner_radius[2],
                    corner_radius[3],
                )
        else:
            radii = (0, 0, 0, 0)
        if not fill:
            self._draw_outline_rect(x, y, width, height, color, border_width, radii)
            return
        if border_color is not None and border_width > 0:
            border_w = border_width * 2
            border_h = border_width * 2
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(
                    x - border_width,
                    y - border_width,
                    width + border_w,
                    height + border_h,
                    border_color,
                    fill=True,
                    border_width=0,
                )
            else:
                expanded_radii = tuple(r + border_width for r in radii)
                self._draw_rounded_rect(
                    x - border_width,
                    y - border_width,
                    width + border_w,
                    height + border_h,
                    border_color,
                    fill=True,
                    border_width=0,
                    radii=expanded_radii,
                )
            inner_x = x + border_width
            inner_y = y + border_width
            inner_w = width - border_w
            inner_h = height - border_h
            if inner_w > 0 and inner_h > 0:
                if all(r == 0 for r in radii):
                    self._draw_sharp_rect(
                        inner_x,
                        inner_y,
                        inner_w,
                        inner_h,
                        color,
                        fill=True,
                        border_width=0,
                    )
                else:
                    inner_radii = tuple(max(0, r - border_width) for r in radii)
                    self._draw_rounded_rect(
                        inner_x,
                        inner_y,
                        inner_w,
                        inner_h,
                        color,
                        fill=True,
                        border_width=0,
                        radii=inner_radii,
                    )
        else:
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(
                    x, y, width, height, color, fill=True, border_width=0
                )
            else:
                self._draw_rounded_rect(
                    x, y, width, height, color, fill=True, border_width=0, radii=radii
                )

    def _draw_outline_rect(self, x, y, width, height, color, border_width, radii):
        if all(r == 0 for r in radii):
            self._draw_sharp_rect(
                x, y, width, height, color, fill=False, border_width=border_width
            )
        else:
            self._draw_rounded_rect(
                x,
                y,
                width,
                height,
                color,
                fill=False,
                border_width=border_width,
                radii=radii,
            )

    def _draw_sharp_rect(self, x, y, width, height, color, fill=True, border_width=1):
        self.simple_shader.use()
        gl.glUniform2f(
            self.simple_shader._get_uniform_location("uScreenSize"),
            float(self.width),
            float(self.height),
        )
        r, g, b, a = self._convert_color(color)
        if not fill:
            self._draw_sharp_rect(x, y, width, border_width, color, True, 0)
            self._draw_sharp_rect(
                x, y + height - border_width, width, border_width, color, True, 0
            )
            self._draw_sharp_rect(
                x,
                y + border_width,
                border_width,
                height - 2 * border_width,
                color,
                True,
                0,
            )
            self._draw_sharp_rect(
                x + width - border_width,
                y + border_width,
                border_width,
                height - 2 * border_width,
                color,
                True,
                0,
            )
        else:
            gl.glUniform4f(
                self.simple_shader._get_uniform_location("uTransform"),
                float(x),
                float(y),
                float(width),
                float(height),
            )
            gl.glUniform4f(
                self.simple_shader._get_uniform_location("uColor"), r, g, b, a
            )
            gl.glBindVertexArray(self.simple_shader.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
        self.simple_shader.unuse()

    def _draw_rounded_rect(
        self, x, y, w, h, color, fill=True, border_width=1, radii=(0, 0, 0, 0)
    ):
        r, g, b, a = self._convert_color(color)
        self.rounded_rect_shader.use()
        gl.glUniform2f(
            self.rounded_rect_shader._get_uniform_location("uScreenSize"),
            self.width,
            self.height,
        )
        gl.glUniform4f(
            self.rounded_rect_shader._get_uniform_location("uTransform"), x, y, w, h
        )
        gl.glUniform4f(
            self.rounded_rect_shader._get_uniform_location("uColor"), r, g, b, a
        )
        gl.glUniform4f(
            self.rounded_rect_shader._get_uniform_location("uCornerRadii"),
            float(radii[0]),
            float(radii[1]),
            float(radii[2]),
            float(radii[3]),
        )
        gl.glUniform2f(
            self.rounded_rect_shader._get_uniform_location("uRectSize"), w, h
        )
        gl.glUniform1f(self.rounded_rect_shader._get_uniform_location("uFeather"), 1.5)
        gl.glUniform1i(
            self.rounded_rect_shader._get_uniform_location("uFill"), 1 if fill else 0
        )
        gl.glUniform1f(
            self.rounded_rect_shader._get_uniform_location("uBorderWidth"),
            border_width if not fill else 0,
        )
        gl.glBindVertexArray(self.rounded_rect_shader.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        self.rounded_rect_shader.unuse()

    # ---------------------------------------------------------------------
    # Triangle helpers (now call draw_polygon)
    # ---------------------------------------------------------------------
    def draw_isosceles_triangle(
        self,
        x: Union[int, float],
        y: Union[int, float],
        width: Union[int, float],
        height: Union[int, float],
        color=None,
        fill=True,
        border_width=1,
        border_color=None,
        surface=None,
        pivot=(0.0, 0.0),
        style=None,
    ):
        if width <= 0 or height <= 0:
            return
        pts = [
            (x + width / 2.0, y),
            (x, y + height),
            (x + width, y + height),
        ]
        self.draw_polygon(
            pts,
            color=color,
            fill=fill,
            border_width=border_width,
            border_color=border_color,
            surface=surface,
            pivot=pivot,
            style=style,
        )

    def draw_equilateral_triangle(
        self,
        x: Union[int, float],
        y: Union[int, float],
        side_length: Union[int, float],
        color=None,
        fill=True,
        border_width=1,
        border_color=None,
        surface=None,
        pivot=(0.0, 0.0),
        style=None,
    ):
        if side_length <= 0:
            return
        height = side_length * math.sqrt(3.0) / 2.0
        pts = [
            (x + side_length / 2.0, y),
            (x, y + height),
            (x + side_length, y + height),
        ]
        self.draw_polygon(
            pts,
            color=color,
            fill=fill,
            border_width=border_width,
            border_color=border_color,
            surface=surface,
            pivot=pivot,
            style=style,
        )

    # ---------------------------------------------------------------------
    # Drawing: Lines
    # ---------------------------------------------------------------------
    def draw_line(self, start_x, start_y, end_x, end_y, color, width=2, surface=None):
        if not self._initialized or not self.simple_shader.program:
            return
        if surface:
            old = self._current_target
            self.set_surface(surface)
        if not (start_x == end_x and start_y == end_y):
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
        vertices = np.array(
            [
                x1 + perp_x,
                y1 + perp_y,
                x1 - perp_x,
                y1 - perp_y,
                x2 - perp_x,
                y2 - perp_y,
                x2 + perp_x,
                y2 + perp_y,
            ],
            dtype=np.float32,
        )
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * 4, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)
        self.simple_shader.use()
        gl.glUniform2f(
            self.simple_shader._get_uniform_location("uScreenSize"),
            self.width,
            self.height,
        )
        gl.glUniform4f(
            self.simple_shader._get_uniform_location("uTransform"), 0, 0, 1, 1
        )
        gl.glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)
        gl.glBindVertexArray(vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1, [vao])
        gl.glDeleteBuffers(1, [vbo])
        gl.glDeleteBuffers(1, [ebo])
        self.simple_shader.unuse()

    def draw_lines(self, points, color, width=2, surface=None):
        for (x1, y1), (x2, y2) in points:
            self.draw_line(x1, y1, x2, y2, color, width, surface)

    # ---------------------------------------------------------------------
    # Drawing: Circles
    # ---------------------------------------------------------------------
    def draw_circle(
        self,
        center_x,
        center_y,
        radius,
        color=None,
        fill=True,
        border_width=1,
        surface=None,
        pivot=(0.5, 0.5),
        style: Optional[Dict[str, Any]] = None,
    ):
        if not self._initialized:
            return
        if surface:
            old = self._current_target
            self.set_surface(surface)

        final_color = color
        final_border_color = None
        final_border_width = border_width
        if style:
            if "solid_color" in style:
                final_color = style["solid_color"]
            if "border_color" in style:
                final_border_color = style["border_color"]
            if "border_width" in style:
                final_border_width = style["border_width"]

        if style and "gradient" in style:
            w = h = radius * 2
            x = center_x - pivot[0] * w
            y = center_y - pivot[1] * h

            self._ensure_temp_fbo(int(w), int(h))
            old_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
            gl.glViewport(0, 0, int(w), int(h))
            old_w, old_h = self.width, self.height
            self.width, self.height = int(w), int(h)

            # Render mask
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_mask"])
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self._draw_circle_fast(
                w / 2,
                h / 2,
                radius,
                (255, 255, 255, 255),
                fill=True,
                border_width=0,
                pivot=(0.5, 0.5),
            )

            # Generate gradient texture
            grad = style["gradient"]
            fill_tex = self._generate_gradient_texture(
                grad,
                int(w),
                int(h),
                style.get("gradient_type", "linear"),
                style.get("gradient_angle", 0.0),
            )
            if fill_tex == 0:
                self._draw_circle_fast(
                    center_x,
                    center_y,
                    radius,
                    final_color,
                    fill,
                    final_border_width,
                    pivot,
                )
                if surface:
                    self.set_surface(old)
                self.width, self.height = old_w, old_h
                gl.glViewport(
                    old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3]
                )
                return

            # Composite
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_composite"])
            gl.glClearColor(0.0, 0.0, 0.0, 0.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self.mask_shader.use()
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, fill_tex)
            gl.glUniform1i(self.mask_shader._get_uniform_location("fillTexture"), 0)
            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._temp["tex_mask"])
            gl.glUniform1i(self.mask_shader._get_uniform_location("maskTexture"), 1)
            gl.glBindVertexArray(self.mask_shader.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
            self.mask_shader.unuse()

            # Border
            if final_border_width > 0 and final_border_color:
                self._draw_circle_fast(
                    w / 2,
                    h / 2,
                    radius,
                    final_border_color,
                    fill=False,
                    border_width=final_border_width,
                    pivot=(0.5, 0.5),
                )

            self.width, self.height = old_w, old_h
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            gl.glViewport(
                old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3]
            )

            self.texture_shader.use()
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._temp["tex_composite"])
            gl.glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
            gl.glUniform2f(
                self.texture_shader._get_uniform_location("uScreenSize"),
                self.width,
                self.height,
            )
            gl.glUniform4f(
                self.texture_shader._get_uniform_location("uTransform"), x, y, w, h
            )
            gl.glBindVertexArray(self.texture_shader.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
            self.texture_shader.unuse()

            if surface:
                self.set_surface(old)
            return

        # Fast path
        self._draw_circle_fast(
            center_x, center_y, radius, final_color, fill, final_border_width, pivot
        )
        if surface:
            self.set_surface(old)

    def _draw_circle_fast(
        self,
        center_x,
        center_y,
        radius,
        color,
        fill=True,
        border_width=1,
        pivot=(0.5, 0.5),
    ):
        if not self._initialized or not self.simple_shader.program:
            return
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
                vertices, indices = self._generate_hollow_circle_geometry(
                    segments, border_width, radius
                )
            vao, vbo, ebo = self._upload_geometry(vertices, indices)
            vertex_count = len(indices)
            self._circle_cache[cache_key] = (vao, vbo, ebo, vertex_count)
        r, g, b, a = self._convert_color(color or (255, 255, 255, 255))
        self.simple_shader.use()
        gl.glUniform2f(
            self.simple_shader._get_uniform_location("uScreenSize"),
            self.width,
            self.height,
        )
        gl.glUniform4f(
            self.simple_shader._get_uniform_location("uTransform"), x, y, width, height
        )
        gl.glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)
        gl.glBindVertexArray(vao)
        gl.glDrawElements(gl.GL_TRIANGLES, vertex_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        self.simple_shader.unuse()

    def _generate_filled_circle_geometry(self, segments):
        segments = int(segments)
        vertices = [0.5, 0.5]
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            vertices.extend([math.cos(angle) * 0.5 + 0.5, math.sin(angle) * 0.5 + 0.5])
        indices = []
        for i in range(1, segments):
            indices.extend([0, i, i + 1])
        indices.extend([0, segments, 1])
        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.uint32)

    def _generate_hollow_circle_geometry(self, segments, border_width, radius):
        segments = int(segments)
        inner_radius = max(0.1, (radius - border_width) / radius * 0.5)
        outer_radius = 0.5
        vertices = []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            vertices.extend(
                [
                    math.cos(angle) * outer_radius + 0.5,
                    math.sin(angle) * outer_radius + 0.5,
                ]
            )
            vertices.extend(
                [
                    math.cos(angle) * inner_radius + 0.5,
                    math.sin(angle) * inner_radius + 0.5,
                ]
            )
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
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW
        )
        gl.glVertexAttribPointer(
            0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * 4, ctypes.c_void_p(0)
        )
        gl.glEnableVertexAttribArray(0)
        gl.glBindVertexArray(0)
        return vao, vbo, ebo

    # ---------------------------------------------------------------------
    # Drawing: Polygons (with gradient fix)
    # ---------------------------------------------------------------------

    def draw_polygon(
    self,
    points: Iterable[
        Union[
            Tuple[Union[int, float], Union[int, float]],
            List[Union[int, float]],
            pygame.Vector2,
            Any,
        ]
    ],
    color=None,
    fill=True,
    border_width: Union[int, float] = 1,
    border_color=None,
    surface=None,
    pivot: Tuple[Union[int, float], Union[int, float]] = (0.0, 0.0),
    style: Optional[Dict[str, Any]] = None,
) -> None:
        if not self._initialized or len(points) < 3:
            return

        # Normalise points
        pts = []
        for p in points:
            if hasattr(p, "x") and hasattr(p, "y"):
                pts.append((float(p.x), float(p.y)))
            else:
                try:
                    x, y = p
                    pts.append((float(x), float(y)))
                except (TypeError, ValueError):
                    raise TypeError(f"Invalid point type: {p}")

        if surface:
            old_target = self._current_target
            self.set_surface(surface)

        # ---- Resolve colours and border ----
        final_color = color
        final_border_color = border_color
        final_border_width = float(border_width)

        if style:
            # Override with style values if present
            if "solid_color" in style:
                final_color = style["solid_color"]
            if "border_color" in style and border_color is None:
                final_border_color = style["border_color"]
            if "border_width" in style:
                final_border_width = float(style["border_width"])
            # Explicit parameters take precedence over style
            if border_color is not None:
                final_border_color = border_color
            if border_width != 1:
                final_border_width = float(border_width)

        # Apply pivot
        px, py = pivot
        pts = [(x + px, y + py) for x, y in pts]

        # If no fill colour is provided, use a default
        if final_color is None and fill:
            final_color = (255, 255, 255, 255)

        # ---- Shadow handling ----
        shadow_obj = style.get("shadow") if style else None
        if shadow_obj is not None:
            if hasattr(shadow_obj, "color"):
                shadow = {
                    "color": shadow_obj.color,
                    "alpha": shadow_obj.alpha,
                    "distance": shadow_obj.distance,
                    "direction": shadow_obj.direction,
                }
            else:
                shadow = shadow_obj
            distance = shadow.get("distance", 0.0)
            alpha = shadow.get("alpha", 0.0)
            if distance > 0 and alpha > 0:
                direction = shadow.get("direction", (0.0, 0.0, 0.0, 0.0))
                dx = (direction[2] - direction[0]) * distance
                dy = (direction[3] - direction[1]) * distance
                shadow_color = shadow.get("color", (0, 0, 0))
                shadow_pts = [(x + dx, y + dy) for x, y in pts]
                shadow_style = {
                    "solid_color": (*shadow_color, int(alpha * 255)),
                    "border_width": 0,
                }
                self.draw_polygon(
                    shadow_pts,
                    fill=True,
                    border_width=0,
                    style=shadow_style,
                    surface=surface,
                    pivot=(0, 0),
                )
            style = style.copy()
            style.pop("shadow", None)

        # ---- Gradient path ----
        if style and "gradient" in style and fill:
            grad = style["gradient"]
            gradient_type = style.get("gradient_type", "linear")
            gradient_angle = style.get("gradient_angle", 0.0)

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            min_x = min(xs)
            max_x = max(xs)
            min_y = min(ys)
            max_y = max(ys)
            w_float = max_x - min_x
            h_float = max_y - min_y

            if w_float <= 0 or h_float <= 0:
                # Degenerate – draw solid fallback
                self._draw_polygon_fast(pts, final_color, fill=True, pivot=(0, 0))
                if final_border_width > 0 and final_border_color is not None:
                    self._draw_polygon_outline(pts, final_border_color, final_border_width, pivot=(0, 0))
                if surface:
                    self.set_surface(old_target)
                return

            w_int = max(1, math.ceil(w_float))
            h_int = max(1, math.ceil(h_float))
            min_x_int = math.floor(min_x)
            min_y_int = math.floor(min_y)
            offset_x = min_x - min_x_int
            offset_y = min_y - min_y_int

            local_points = [(x - min_x_int, y - min_y_int) for x, y in pts]

            self._ensure_temp_fbo(w_int, h_int)
            old_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
            gl.glViewport(0, 0, w_int, h_int)
            old_w, old_h = self.width, self.height
            self.width, self.height = w_int, h_int

            # 1. Render white mask
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_mask"])
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            self._draw_polygon_fast(
                local_points,
                (255, 255, 255, 255),
                fill=True,
                pivot=(0, 0),
            )

            # 2. Generate gradient texture
            fill_tex = self._generate_gradient_texture(
                grad,
                w_int,
                h_int,
                gradient_type=gradient_type,
                angle=gradient_angle,
                scale_x=w_float,
                scale_y=h_float,
                offset_x=offset_x,
                offset_y=offset_y,
            )

            if fill_tex == 0:
                # Fallback to solid
                self._draw_polygon_fast(pts, final_color, fill=True, pivot=(0, 0))
                if final_border_width > 0 and final_border_color is not None:
                    self._draw_polygon_outline(pts, final_border_color, final_border_width, pivot=(0, 0))
                self.width, self.height = old_w, old_h
                gl.glViewport(old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3])
                if surface:
                    self.set_surface(old_target)
                return

            # 3. Composite
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_composite"])
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

            self.mask_shader.use()
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, fill_tex)
            gl.glUniform1i(self.mask_shader._get_uniform_location("fillTexture"), 0)

            gl.glActiveTexture(gl.GL_TEXTURE1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._temp["tex_mask"])
            gl.glUniform1i(self.mask_shader._get_uniform_location("maskTexture"), 1)

            gl.glBindVertexArray(self.mask_shader.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
            self.mask_shader.unuse()

            # 4. Restore and blit composite (without border – border will be drawn on top)
            self.width, self.height = old_w, old_h
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            gl.glViewport(old_viewport[0], old_viewport[1], old_viewport[2], old_viewport[3])

            self.texture_shader.use()
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._temp["tex_composite"])
            gl.glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
            gl.glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), float(self.width), float(self.height))
            gl.glUniform4f(
                self.texture_shader._get_uniform_location("uTransform"),
                float(min_x_int),
                float(min_y_int),
                float(w_int),
                float(h_int),
            )
            gl.glBindVertexArray(self.texture_shader.vao)
            gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
            gl.glBindVertexArray(0)
            self.texture_shader.unuse()

            # 5. Draw border on top (in world space, using line loop)
            if final_border_width > 0 and final_border_color is not None:
                self._draw_polygon_outline(pts, final_border_color, final_border_width, pivot=(0, 0))

            if surface:
                self.set_surface(old_target)
            return

        # ---- Fast path (no gradient) ----
        # Draw filled polygon
        if fill and final_color is not None:
            self._draw_polygon_fast(pts, final_color, fill=True, pivot=(0, 0))

        # Draw outline if needed
        if final_border_width > 0 and final_border_color is not None:
            self._draw_polygon_outline(pts, final_border_color, final_border_width, pivot=(0, 0))

        if surface:
            self.set_surface(old_target)
    
    def _draw_polygon_outline(self, points, color, border_width, pivot=(0.0, 0.0)):
        """
        Draw a clean polygon outline using GL_LINE_LOOP.
        This avoids shrinking geometry issues.
        """
        if not self._initialized or len(points) < 3 or border_width <= 0:
            return

        points = [(x + pivot[0], y + pivot[1]) for x, y in points]

        # Build vertices (just the polygon corners)
        vertices = []
        for x, y in points:
            vertices.extend([x, y])

        vertices_arr = np.array(vertices, dtype=np.float32)

        # For GL_LINE_LOOP, we need indices that form a closed loop
        indices = np.array(list(range(len(points))) + [0], dtype=np.uint32)

        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        ebo = gl.glGenBuffers(1)

        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices_arr.nbytes, vertices_arr, gl.GL_STATIC_DRAW)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 2 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)

        r, g, b, a = self._convert_color(color)

        self.simple_shader.use()
        gl.glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        gl.glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 0, 0, 1, 1)
        gl.glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)

        gl.glLineWidth(float(border_width))
        gl.glBindVertexArray(vao)
        gl.glDrawElements(gl.GL_LINE_LOOP, len(indices), gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        # Reset line width
        gl.glLineWidth(1.0)

        gl.glDeleteVertexArrays(1, [vao])
        gl.glDeleteBuffers(1, [vbo])
        gl.glDeleteBuffers(1, [ebo])

        self.simple_shader.unuse()
    
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

    def _draw_polygon_fast(self, points, color, fill=True, border_width=1, pivot=(0.0, 0.0)):
        """Draw a filled polygon using the simple shader."""
        if not self._initialized or len(points) < 3:
            return

        points = [(x + pivot[0], y + pivot[1]) for x, y in points]

        # Only fill is supported here; outlines are handled separately
        if not fill:
            return

        vertices, indices = self._generate_filled_polygon_geometry(points)
        vao, vbo, ebo = self._upload_geometry(vertices, indices)
        vertex_count = len(indices)

        xs, ys = zip(*points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width, height = max_x - min_x, max_y - min_y

        r, g, b, a = self._convert_color(color or (255, 255, 255, 255))

        self.simple_shader.use()
        gl.glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), self.width, self.height)
        gl.glUniform4f(self.simple_shader._get_uniform_location("uTransform"), min_x, min_y, width, height)
        gl.glUniform4f(self.simple_shader._get_uniform_location("uColor"), r, g, b, a)
        gl.glBindVertexArray(vao)
        gl.glDrawElements(gl.GL_TRIANGLES, vertex_count, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1, [vao])
        gl.glDeleteBuffers(1, [vbo])
        gl.glDeleteBuffers(1, [ebo])
        self.simple_shader.unuse()
    
    # ---------------------------------------------------------------------
    # Gradient texture generation (with offset fix)
    # ---------------------------------------------------------------------
    def _generate_gradient_texture(
        self,
        color_keys: Union[ColorKeys, List[Tuple[int, int, int, float]], List[Color]],
        width: Union[int, float],
        height: Union[int, float],
        gradient_type: Literal["linear", "radial", "conic"] = "linear",
        angle: Union[int, float] = 0.0,
        scale_x: Union[int, float] = 1.0,
        scale_y: Union[int, float] = 1.0,
        offset_x: Union[int, float] = 0.0,
        offset_y: Union[int, float] = 0.0,
    ) -> int:
        w = int(width)
        h = int(height)
        if w <= 0 or h <= 0:
            return 0

        # Normalise color_keys to hashable tuple
        if isinstance(color_keys, list):
            key_colors = tuple(
                tuple(c) if isinstance(c, (tuple, list)) else (c.r, c.g, c.b, c.a)
                for c in color_keys
            )
        elif isinstance(color_keys, ColorKeys):
            key_colors = tuple(
                (k, (v.r, v.g, v.b, v.a)) for k, v in sorted(color_keys.keys.items())
            )
        else:
            raise TypeError("color_keys must be a list or ColorKeys")

        cache_key = (
            key_colors,
            w,
            h,
            gradient_type,
            round(float(angle), 4),
            round(float(scale_x), 4),
            round(float(scale_y), 4),
            round(float(offset_x), 4),
            round(float(offset_y), 4),
        )

        if cache_key in self._gradient_cache:
            self._gradient_cache.move_to_end(cache_key)
            return self._gradient_cache[cache_key]

        if isinstance(color_keys, list):
            color_keys = ColorKeys(color_keys)
        elif not isinstance(color_keys, ColorKeys):
            raise TypeError("color_keys must be a list or ColorKeys")

        surf = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        rad = math.radians(float(angle))
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        first_col = (
            next(iter(color_keys.keys.values()))
            if color_keys.keys
            else Color(255, 255, 255, 1.0)
        )

        sx = float(scale_x)
        sy = float(scale_y)
        ox = float(offset_x)
        oy = float(offset_y)

        for y in range(h):
            for x in range(w):
                # Correct mapping: pixel (x,y) is at world (min_int + x, min_int + y)
                # Polygon's actual min is at (min_int + offset_x, min_int + offset_y)
                # So u = (x - offset_x) / scale_x, v = (y - offset_y) / scale_y
                u = (x - ox) / sx if sx != 0 else 0.5
                v = (y - oy) / sy if sy != 0 else 0.5

                if gradient_type == "linear":
                    t = u * cos_a + v * sin_a
                elif gradient_type == "radial":
                    du = u - 0.5
                    dv = v - 0.5
                    t = math.hypot(du, dv) * 1.414
                elif gradient_type == "conic":
                    du = u - 0.5
                    dv = v - 0.5
                    t = (math.atan2(dv, du) / (2 * math.pi) + 0.5) % 1.0
                else:
                    t = u

                col = color_keys.get_color(t)
                if col is None:
                    col = first_col
                surf.set_at((x, y), (col.r, col.g, col.b, int(col.a * 255)))

        tex = self._surface_to_texture(surf)
        if tex == 0:
            return 0

        self._gradient_cache[cache_key] = tex
        if len(self._gradient_cache) > self._gradient_cache_max_size:
            oldest_key, oldest_tex = self._gradient_cache.popitem(last=False)
            gl.glDeleteTextures(1, [oldest_tex])

        return tex

    # ---------------------------------------------------------------------
    # Temporary FBO management
    # ---------------------------------------------------------------------
    def _ensure_temp_fbo(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        if (
            self._temp["fbo_mask"] is not None
            and self._temp["fbo_composite"] is not None
            and self._temp["width"] >= width
            and self._temp["height"] >= height
        ):
            return

        # Delete old resources
        for key in (
            "fbo_mask",
            "fbo_composite",
            "tex_mask",
            "tex_composite",
            "rb_mask",
            "rb_composite",
        ):
            if self._temp[key] is not None:
                if key.startswith("fbo"):
                    gl.glDeleteFramebuffers(1, [self._temp[key]])
                elif key.startswith("tex"):
                    gl.glDeleteTextures(1, [self._temp[key]])
                elif key.startswith("rb"):
                    gl.glDeleteRenderbuffers(1, [self._temp[key]])
                self._temp[key] = None

        self._temp["width"] = max(1, width)
        self._temp["height"] = max(1, height)

        # Create FBOs
        self._temp["fbo_mask"] = gl.glGenFramebuffers(1)
        self._temp["fbo_composite"] = gl.glGenFramebuffers(1)

        # Create textures
        self._temp["tex_mask"] = gl.glGenTextures(1)
        self._temp["tex_composite"] = gl.glGenTextures(1)

        # Create renderbuffers
        self._temp["rb_mask"] = gl.glGenRenderbuffers(1)
        self._temp["rb_composite"] = gl.glGenRenderbuffers(1)

        w, h = self._temp["width"], self._temp["height"]

        # Set up both textures
        for tex in (self._temp["tex_mask"], self._temp["tex_composite"]):
            gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
            gl.glTexImage2D(
                gl.GL_TEXTURE_2D,
                0,
                gl.GL_RGBA,
                w,
                h,
                0,
                gl.GL_RGBA,
                gl.GL_UNSIGNED_BYTE,
                None,
            )
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE
            )
            gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE
            )

        # Set up renderbuffers
        for rb in (self._temp["rb_mask"], self._temp["rb_composite"]):
            gl.glBindRenderbuffer(gl.GL_RENDERBUFFER, rb)
            gl.glRenderbufferStorage(gl.GL_RENDERBUFFER, gl.GL_DEPTH24_STENCIL8, w, h)

        # Set up mask FBO
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_mask"])
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D,
            self._temp["tex_mask"],
            0,
        )
        gl.glFramebufferRenderbuffer(
            gl.GL_FRAMEBUFFER,
            gl.GL_DEPTH_STENCIL_ATTACHMENT,
            gl.GL_RENDERBUFFER,
            self._temp["rb_mask"],
        )
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print(
                f"Mask FBO incomplete! {hex(gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER))}"
            )

        # Set up composite FBO
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._temp["fbo_composite"])
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER,
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D,
            self._temp["tex_composite"],
            0,
        )
        gl.glFramebufferRenderbuffer(
            gl.GL_FRAMEBUFFER,
            gl.GL_DEPTH_STENCIL_ATTACHMENT,
            gl.GL_RENDERBUFFER,
            self._temp["rb_composite"],
        )
        if gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) != gl.GL_FRAMEBUFFER_COMPLETE:
            print(
                f"Composite FBO incomplete! {hex(gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER))}"
            )

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    # ---------------------------------------------------------------------
    # Text
    # ---------------------------------------------------------------------
    def draw_text(
        self,
        text: str,
        x: int|float,
        y: int|float,
        color,
        font: pygame.font.Font,
        surface: Optional[pygame.Surface] = None,
        pivot: Tuple[int|float, int|float] = (0.0, 0.0),
        flip: Tuple[bool, bool] = (False, False),
        rotate: int|float = 0.0,
        style: Optional[Dict] = None,
        *args,
        **kwargs,
    ) -> None:
        if not self._initialized:
            return

        def _render_text_at(pos_x, pos_y, col, fnt, flp=flip, rot=rotate):
            try:
                if isinstance(col, pygame.Color):
                    pygame_color = col
                elif isinstance(col, Color):
                    pygame_color = pygame.Color(col.r, col.g, col.b, int(col.a * 255))
                elif isinstance(col, (tuple, list)):
                    if len(col) >= 3:
                        r, g, b = int(col[0]), int(col[1]), int(col[2])
                        a = int(col[3]) if len(col) > 3 else 255
                        pygame_color = pygame.Color(r, g, b, a)
                    else:
                        pygame_color = pygame.Color(255, 255, 255)
                elif isinstance(col, int):
                    pygame_color = pygame.Color(col, col, col)
                else:
                    pygame_color = pygame.Color(255, 255, 255)
            except Exception as e:
                print(f"Colour conversion error: {e}, falling back to white")
                pygame_color = pygame.Color(255, 255, 255)

            r, g, b, a = pygame_color.r, pygame_color.g, pygame_color.b, pygame_color.a
            is_bold = kwargs.get("bold", False)
            is_italic = kwargs.get("italic", False)

            if isinstance(fnt, tuple):
                fnt = pygame.font.SysFont(fnt[0], fnt[1], is_bold, is_italic)

            cache_key = (text, fnt, (r, g, b), (is_bold, is_italic))
            now = time.time()

            if cache_key in self._text_cache:
                tex, (tw, th) = self._text_cache[cache_key]
                if tex == 0 or not gl.glIsTexture(tex):
                    text_surface = fnt.render(text, True, pygame_color)
                    tex = self._surface_to_texture(text_surface)
                    if tex == 0:
                        return
                    tw, th = text_surface.get_size()
                    self._text_cache[cache_key] = (tex, (tw, th))
                self._text_cache_last_used[cache_key] = now
            else:
                text_surface = fnt.render(text, True, pygame_color)
                tex = self._surface_to_texture(text_surface)
                if tex == 0:
                    return
                tw, th = text_surface.get_size()
                self._text_cache[cache_key] = (tex, (tw, th))
                self._text_cache_last_used[cache_key] = now

            if now - self._last_text_cache_cleanup >= self._text_cache_cleanup_interval:
                self._cleanup_text_cache(now)

            pos_x = pos_x - int(pivot[0] * tw)
            pos_y = pos_y - int(pivot[1] * th)

            old_target = None
            if surface:
                old_target = self._current_target
                self.set_surface(surface)

            if flp == (False, False) and rot == 0.0:
                self.texture_shader.use()
                gl.glUniform2f(
                    self.texture_shader._get_uniform_location("uScreenSize"),
                    self.width,
                    self.height,
                )
                gl.glUniform4f(
                    self.texture_shader._get_uniform_location("uTransform"),
                    pos_x,
                    pos_y,
                    tw,
                    th,
                )
                gl.glActiveTexture(gl.GL_TEXTURE0)
                gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
                gl.glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
                gl.glBindVertexArray(self.texture_shader.vao)
                gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
                gl.glBindVertexArray(0)
                self.texture_shader.unuse()
            else:
                center_x = pos_x + tw / 2.0
                center_y = pos_y + th / 2.0
                w2, h2 = tw / 2.0, th / 2.0
                corners = [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]
                uvs = [
                    (0.0 if not flp[0] else 1.0, 0.0 if not flp[1] else 1.0),
                    (1.0 if not flp[0] else 0.0, 0.0 if not flp[1] else 1.0),
                    (1.0 if not flp[0] else 0.0, 1.0 if not flp[1] else 0.0),
                    (0.0 if not flp[0] else 1.0, 1.0 if not flp[1] else 0.0),
                ]
                if rot != 0.0:
                    rad = math.radians(rot)
                    cos_a, sin_a = math.cos(rad), math.sin(rad)
                    corners = [
                        (cx * cos_a - cy * sin_a, cx * sin_a + cy * cos_a)
                        for (cx, cy) in corners
                    ]
                vertices = []
                for (cx, cy), (u, v) in zip(corners, uvs):
                    vertices.extend([center_x + cx, center_y + cy, u, v])
                vertices_arr = np.array(vertices, dtype=np.float32)
                indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

                vao = gl.glGenVertexArrays(1)
                vbo = gl.glGenBuffers(1)
                ebo = gl.glGenBuffers(1)
                gl.glBindVertexArray(vao)
                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
                gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    vertices_arr.nbytes,
                    vertices_arr,
                    gl.GL_STATIC_DRAW,
                )
                gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, ebo)
                gl.glBufferData(
                    gl.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    gl.GL_STATIC_DRAW,
                )
                gl.glVertexAttribPointer(
                    0,
                    2,
                    gl.GL_FLOAT,
                    gl.GL_FALSE,
                    4 * vertices_arr.itemsize,
                    ctypes.c_void_p(0),
                )
                gl.glEnableVertexAttribArray(0)
                gl.glVertexAttribPointer(
                    1,
                    2,
                    gl.GL_FLOAT,
                    gl.GL_FALSE,
                    4 * vertices_arr.itemsize,
                    ctypes.c_void_p(2 * vertices_arr.itemsize),
                )
                gl.glEnableVertexAttribArray(1)

                self.texture_shader.use()
                gl.glUniform2f(
                    self.texture_shader._get_uniform_location("uScreenSize"),
                    self.width,
                    self.height,
                )
                gl.glUniform4f(
                    self.texture_shader._get_uniform_location("uTransform"), 0, 0, 1, 1
                )
                gl.glActiveTexture(gl.GL_TEXTURE0)
                gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
                gl.glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
                gl.glBindVertexArray(vao)
                gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
                gl.glBindVertexArray(0)
                gl.glDeleteVertexArrays(1, [vao])
                gl.glDeleteBuffers(1, [vbo])
                gl.glDeleteBuffers(1, [ebo])
                self.texture_shader.unuse()

            if surface:
                self.set_surface(old_target)

        # Shadow handling
        if style and "shadow" in style:
            shadow = style["shadow"]
            if isinstance(shadow, UiShadow):
                shadow_dict = {
                    "color": shadow.color,
                    "alpha": shadow.alpha,
                    "distance": shadow.distance,
                    "direction": shadow.direction,
                }
            else:
                shadow_dict = shadow

            direction = shadow_dict.get("direction", (0.0, 0.0, 0.0, 0.0))
            distance = shadow_dict.get("distance", 0.0)
            alpha = shadow_dict.get("alpha", 0.5)

            if distance > 0 and alpha > 0:
                dx = (direction[2] - direction[0]) * distance
                dy = (direction[3] - direction[1]) * distance
                shadow_color = shadow_dict.get("color", (0, 0, 0))
                shadow_col = pygame.Color(
                    max(0, min(255, shadow_color[0])),
                    max(0, min(255, shadow_color[1])),
                    max(0, min(255, shadow_color[2])),
                    int(max(0, min(1.0, alpha)) * 255),
                )
                _render_text_at(x + dx, y + dy, shadow_col, font, flp=flip, rot=rotate)

            style = style.copy()
            style.pop("shadow", None)

        _render_text_at(x, y, color, font, flp=flip, rot=rotate)

    def draw_rich_text(
        self, text, x, y, default_color, font, surface=None, pivot=(0.0, 0.0), **kwargs
    ):
        if not text:
            return
        from ..ui.elements.labels import render_rich_text

        render_rich_text(text, self, x, y, default_color, font, pivot, **kwargs)

    def draw_rich_text_line(self, line, x, y, default_color, font, surface=None):
        if not line:
            return
        from ..ui.elements.labels import render_rich_text_line

        render_rich_text_line(line, self, x, y, default_color, font)

    def _cleanup_text_cache(self, now: float):
        keys_to_delete = []
        for key, last_used in self._text_cache_last_used.items():
            if now - last_used > self._text_cache_timeout:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            tex, _ = self._text_cache.pop(key, (None, None))
            if tex:
                gl.glDeleteTextures(1, [tex])
            self._text_cache_last_used.pop(key, None)
        self._last_text_cache_cleanup = now

    def _cleanup_texture_cache(self, time_dur=5.0, force_cleanup=False):
        now = time.time()
        if not force_cleanup and (
            now - self._last_texture_cache_cleanup < self._texture_cache_timeout
        ):
            return
        for surface, inner_cache in list(self._texture_cache.items()):
            expired_sub_keys = []
            for sub_key, (tex, size, last_use) in inner_cache.items():
                if force_cleanup or (now - last_use > time_dur):
                    gl.glDeleteTextures(1, [tex])
                    expired_sub_keys.append(sub_key)
            for key in expired_sub_keys:
                del inner_cache[key]
            if not inner_cache:
                del self._texture_cache[surface]
        self._last_texture_cache_cleanup = now

    # ---------------------------------------------------------------------
    # Surface blitting
    # ---------------------------------------------------------------------
    def draw_surface(self, surface, x, y, pivot=(0.0, 0.0), use_cache=True):
        self.blit(surface, (x, y), pivot=pivot, use_cache=use_cache)

    def blit(
        self, source, dest, area=None, special_flags=0, pivot=(0.0, 0.0), use_cache=True
    ):
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
        gl.glUniform2f(
            self.texture_shader._get_uniform_location("uScreenSize"),
            self.width,
            self.height,
        )
        gl.glUniform4f(
            self.texture_shader._get_uniform_location("uTransform"),
            x,
            y,
            dest_w,
            dest_h,
        )
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glBindVertexArray(self.texture_shader.vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)
        self.texture_shader.unuse()

    def fill_screen(self, color):
        r, g, b, a = self._convert_color(color)
        gl.glClearColor(r, g, b, a)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def clear(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # ---------------------------------------------------------------------
    # Particles
    # ---------------------------------------------------------------------
    def render_particles(self, particle_data, camera):
        if not self._initialized or not self.particle_shader.program:
            return
        active = particle_data["active_count"]
        if active == 0:
            return
        self._ensure_particle_capacity(active)
        world_pos = particle_data["positions"]
        screen_pos = np.zeros((active, 2), dtype=np.float32)
        for i in range(active):
            sp = camera.world_to_screen(world_pos[i])
            screen_pos[i] = [sp.x, sp.y]
        sizes = camera.convert_size_zoom_list(
            particle_data["sizes"][:active], "ndarray"
        )
        alphas = particle_data["alphas"][:active] / 255.0
        colors = particle_data["colors"][:active] / 255.0
        instance_data = np.zeros((active, 4), dtype=np.float32)
        instance_data[:, 0] = screen_pos[:, 0]
        instance_data[:, 1] = screen_pos[:, 1]
        instance_data[:, 2] = np.maximum(2.0, sizes)
        instance_data[:, 3] = alphas
        colour_data = np.zeros((active, 4), dtype=np.float32)
        colour_data[:, 0:3] = colors
        colour_data[:, 3] = 1.0

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, instance_data.nbytes, instance_data, gl.GL_DYNAMIC_DRAW
        )
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, colour_data.nbytes, colour_data, gl.GL_DYNAMIC_DRAW
        )

        self.particle_shader.use()
        gl.glUniform2f(
            self.particle_shader._get_uniform_location("uScreenSize"),
            self.width,
            self.height,
        )
        gl.glBindVertexArray(self.particle_shader.vao)
        gl.glDrawArraysInstanced(gl.GL_POINTS, 0, 1, active)
        gl.glBindVertexArray(0)
        self.particle_shader.unuse()

    def _ensure_particle_capacity(self, required):
        if required <= self._max_particles:
            return
        new_size = 1
        while new_size < required:
            new_size *= 2
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, new_size * 4 * 4, None, gl.GL_DYNAMIC_DRAW)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, new_size * 4 * 4, None, gl.GL_DYNAMIC_DRAW)
        self._max_particles = new_size

    # ---------------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------------
    def cleanup(self):
        if not self._initialized:
            return
        for shader in [
            self.simple_shader,
            self.texture_shader,
            self.particle_shader,
            self.filter_shader,
            self.rounded_rect_shader,
            self.mask_shader,
        ]:
            if shader and shader.program:
                gl.glDeleteProgram(shader.program)
        if self._filter_framebuffer:
            gl.glDeleteFramebuffers(1, [self._filter_framebuffer])
        if self._filter_texture:
            gl.glDeleteTextures(1, [self._filter_texture])
        if self._filter_renderbuffer:
            gl.glDeleteRenderbuffers(1, [self._filter_renderbuffer])
        for vao, vbo, ebo, _ in self._circle_cache.values():
            gl.glDeleteVertexArrays(1, [vao])
            gl.glDeleteBuffers(1, [vbo])
            gl.glDeleteBuffers(1, [ebo])
        for vao, vbo, ebo, _ in self._polygon_cache.values():
            gl.glDeleteVertexArrays(1, [vao])
            gl.glDeleteBuffers(1, [vbo])
            gl.glDeleteBuffers(1, [ebo])
        for tex in self._gradient_cache.values():
            gl.glDeleteTextures(1, [tex])
        self._cleanup_texture_cache(force_cleanup=True)
        self._gradient_cache.clear()
        self._circle_cache.clear()
        self._polygon_cache.clear()
        self._texture_cache.clear()
        self._text_cache.clear()
        if self._temp:
            if self._temp.get("fbo_mask"):
                gl.glDeleteFramebuffers(1, [self._temp["fbo_mask"]])
            if self._temp.get("tex_mask"):
                gl.glDeleteTextures(1, [self._temp["tex_mask"]])
            if self._temp.get("rb_mask"):
                gl.glDeleteRenderbuffers(1, [self._temp["rb_mask"]])
        self._initialized = False

    def set_blend_mode(self, mode: str):
        if mode == "normal":
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        elif mode == "add":
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        elif mode == "multiply":
            gl.glBlendFunc(gl.GL_DST_COLOR, gl.GL_ZERO)
        elif mode == "screen":
            gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE_MINUS_SRC_COLOR)
        else:
            print(f"Unknown blend mode: {mode}")
