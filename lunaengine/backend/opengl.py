import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

class OpenGLRenderer:
    """
    OpenGL-based hardware-accelerated renderer for LunaEngine
    
    LOCATION: lunaengine/backend/opengl.py
    
    DESCRIPTION:
    Provides high-performance 2D rendering using OpenGL with shader support.
    Converts pygame surfaces to OpenGL textures and renders them using custom
    shaders for optimal performance.
    
    FEATURES:
    - Hardware-accelerated 2D rendering
    - Custom vertex and fragment shaders
    - Texture-based sprite rendering
    - Alpha blending and transparency support
    
    LIBRARIES USED:
    - pygame: Surface creation and image processing
    - OpenGL.GL: Core OpenGL functionality
    - OpenGL.GL.shaders: Shader compilation and management
    - numpy: Vertex data and matrix operations
    
    USAGE:
    >>> renderer = OpenGLRenderer(800, 600)
    >>> renderer.initialize()
    >>> renderer.draw_surface(sprite_surface, x, y)
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize OpenGL renderer with specified dimensions
        
        ARGS:
            width: Screen width in pixels
            height: Screen height in pixels
        """
        self.width = width
        self.height = height
        self.program = None
        self.quad_vao = None
        self.quad_vbo = None
        
    def initialize(self):
        """Initialize OpenGL context and setup shaders"""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        
        # Create a simple shader program for 2D rendering
        self._create_shaders()
        self._setup_quad_geometry()
        
    def _create_shaders(self):
        """Create basic shaders for 2D rendering"""
        vertex_shader_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        out vec2 TexCoord;
        uniform vec2 uScreenSize;
        void main() {
            vec2 normalizedPos = (aPos / uScreenSize) * 2.0 - 1.0;
            normalizedPos.y = -normalizedPos.y; // Flip Y coordinate
            gl_Position = vec4(normalizedPos, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        
        fragment_shader_source = """
        #version 330 core
        in vec2 TexCoord;
        out vec4 FragColor;
        uniform sampler2D uTexture;
        uniform vec4 uColor;
        uniform int uUseTexture;
        void main() {
            if (uUseTexture == 1) {
                FragColor = texture(uTexture, TexCoord);
            } else {
                FragColor = uColor;
            }
        }
        """
        
        try:
            vertex_shader = compileShader(vertex_shader_source, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_shader_source, GL_FRAGMENT_SHADER)
            self.program = compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"Shader compilation failed: {e}")
            self.program = None
        
    def _setup_quad_geometry(self):
        """Setup quad geometry for rendering"""
        # Vertex data for a quad [x, y, u, v]
        vertices = np.array([
            # positions   # texCoords
            0.0, 1.0,    0.0, 1.0,  # top-left
            1.0, 1.0,    1.0, 1.0,  # top-right
            1.0, 0.0,    1.0, 0.0,  # bottom-right
            
            1.0, 0.0,    1.0, 0.0,  # bottom-right
            0.0, 0.0,    0.0, 0.0,  # bottom-left
            0.0, 1.0,    0.0, 1.0   # top-left
        ], dtype=np.float32)
        
        if self.program:
            self.quad_vao = glGenVertexArrays(1)
            self.quad_vbo = glGenBuffers(1)
            
            glBindVertexArray(self.quad_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            
            # Position attribute
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Texture coordinate attribute
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
            glEnableVertexAttribArray(1)
            
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)
        
    def begin_frame(self):
        """Begin rendering frame"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
    def end_frame(self):
        """End rendering frame"""
        pass
        
    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        """Convert pygame surface to OpenGL texture"""
        texture_data = pygame.image.tostring(surface, "RGBA", True)
        width, height = surface.get_size()
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        return texture_id
        
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        """Draw a pygame surface using OpenGL"""
        if self.program is None or self.quad_vao is None:
            return
            
        width, height = surface.get_size()
        texture_id = self._surface_to_texture(surface)
        
        glUseProgram(self.program)
        
        # Set uniforms
        screen_size_loc = glGetUniformLocation(self.program, "uScreenSize")
        glUniform2f(screen_size_loc, self.width, self.height)
        
        use_texture_loc = glGetUniformLocation(self.program, "uUseTexture")
        glUniform1i(use_texture_loc, 1)
        
        # Set up transformation for this specific surface
        model = np.eye(4, dtype=np.float32)
        model[0, 0] = width
        model[1, 1] = height
        model[3, 0] = x
        model[3, 1] = y
        
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        
        # Cleanup
        glDeleteTextures(1, [texture_id])
        glBindVertexArray(0)
        glUseProgram(0)
        
    def draw_rect(self, x: int, y: int, width: int, height: int, color: tuple):
        """Draw a colored rectangle"""
        if self.program is None or self.quad_vao is None:
            return
            
        # Create a temporary surface for the rectangle
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill(color)
        self.draw_surface(surface, x, y)