"""
OpenGL-based hardware-accelerated renderer for LunaEngine - SIMPLE FIXED VERSION
"""

import pygame
import numpy as np
from typing import Tuple, Dict, Any, List

# Check if OpenGL is available
try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("OpenGL not available - falling back to software rendering")

class ShaderProgram:
    """Generic shader program for 2D rendering"""
    
    def __init__(self, vertex_source, fragment_source):
        self.program = None
        self.vao = None
        self.vbo = None
        self._create_shaders(vertex_source, fragment_source)
        if self.program:
            self._setup_geometry()
    
    def _create_shaders(self, vertex_source, fragment_source):
        """Compile shaders"""
        try:
            vertex_shader = compileShader(vertex_source, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_source, GL_FRAGMENT_SHADER)
            self.program = compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"Shader compilation failed: {e}")
            self.program = None
    
    def _setup_geometry(self):
        """Setup basic quad geometry"""
        # Vertex data: position (x, y), texture coordinates (s, t)
        vertices = np.array([
            # positions   # texture coords
             0.0,  0.0,  0.0, 0.0,  # bottom-left
             1.0,  0.0,  1.0, 0.0,  # bottom-right
             1.0,  1.0,  1.0, 1.0,  # top-right
             0.0,  1.0,  0.0, 1.0,  # top-left
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
        
        # Position attribute
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Texture coordinate attribute
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * vertices.itemsize, ctypes.c_void_p(2 * vertices.itemsize))
        glEnableVertexAttribArray(1)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

class ParticleShader(ShaderProgram):
    """Shader for particle rendering with circles"""
    
    def __init__(self):
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        uniform vec2 uScreenSize;
        uniform vec4 uParticleData; // x, y, size, _
        
        void main() {
            // Convert to pixel coordinates
            vec2 pixelPos = aPos * uParticleData.z + uParticleData.xy;
            
            // Convert to normalized device coordinates
            vec2 ndc = vec2(
                (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
                (1.0 - (pixelPos.y / uScreenSize.y)) * 2.0 - 1.0
            );
            
            gl_Position = vec4(ndc, 0.0, 1.0);
            gl_PointSize = uParticleData.z; // Set point size for circle rendering
        }
        """
        
        fragment_source = """
        #version 330 core
        out vec4 FragColor;
        uniform vec4 uColor;
        
        void main() {
            // Create circle shape using distance from center
            vec2 coord = gl_PointCoord - vec2(0.5);
            if (length(coord) > 0.5) {
                discard;
            }
            FragColor = uColor;
        }
        """
        
        super().__init__(vertex_source, fragment_source)
    
    def _setup_geometry(self):
        """Setup simple point geometry for particles"""
        # Simple point vertices
        vertices = np.array([0.0, 0.0], dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        
        glBindVertexArray(self.vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        # Position attribute
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

class SimpleShader(ShaderProgram):
    """Simple shader for solid color rendering"""
    
    def __init__(self):
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        uniform vec2 uScreenSize;
        uniform vec4 uTransform; // x, y, width, height
        
        void main() {
            // Convert to pixel coordinates
            vec2 pixelPos = aPos * uTransform.zw + uTransform.xy;
            
            // Convert to normalized device coordinates
            // Flip Y axis to match Pygame coordinate system
            vec2 ndc = vec2(
                (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
                (1.0 - (pixelPos.y / uScreenSize.y)) * 2.0 - 1.0
            );
            
            gl_Position = vec4(ndc, 0.0, 1.0);
        }
        """
        
        fragment_source = """
        #version 330 core
        out vec4 FragColor;
        uniform vec4 uColor;
        
        void main() {
            FragColor = uColor;
        }
        """
        
        super().__init__(vertex_source, fragment_source)

class TextureShader(ShaderProgram):
    """Shader for textured rendering"""
    
    def __init__(self):
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        
        out vec2 TexCoord;
        uniform vec2 uScreenSize;
        uniform vec4 uTransform; // x, y, width, height
        
        void main() {
            // Convert to pixel coordinates
            vec2 pixelPos = aPos * uTransform.zw + uTransform.xy;
            
            // Convert to normalized device coordinates
            // Flip Y axis to match Pygame coordinate system
            vec2 ndc = vec2(
                (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
                (1.0 - (pixelPos.y / uScreenSize.y)) * 2.0 - 1.0
            );
            
            gl_Position = vec4(ndc, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        
        fragment_source = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        uniform sampler2D uTexture;
        
        void main() {
            FragColor = texture(uTexture, TexCoord);
        }
        """
        
        super().__init__(vertex_source, fragment_source)

class OpenGLRenderer:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.simple_shader = None
        self.texture_shader = None
        self.particle_shader = None
        self._initialized = False
        
    def initialize(self):
        """Initialize OpenGL context and shaders"""
        if not OPENGL_AVAILABLE:
            return False
            
        print(f"Initializing OpenGL renderer for {self.width}x{self.height}...")
        
        # Set up OpenGL state
        glDisable(GL_FRAMEBUFFER_SRGB) # Disable sRGB for compatibility
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.3, 1.0)
        glEnable(GL_PROGRAM_POINT_SIZE)  # IMPORTANT: Enable point size
        
        # Initialize shaders
        self.simple_shader = SimpleShader()
        self.texture_shader = TextureShader()
        self.particle_shader = ParticleShader()
        
        if not self.simple_shader.program or not self.texture_shader.program or not self.particle_shader.program:
            print("Shader initialization failed")
            return False
        
        self._initialized = True
        print("OpenGL renderer initialized successfully")
        return True
        
    def begin_frame(self):
        """Begin rendering frame"""
        if not self._initialized:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
    def end_frame(self):
        """End rendering frame"""
        if not self._initialized:
            return
        pygame.display.flip()
    
    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        """Convert pygame surface to OpenGL texture"""
        # Convert surface to string (NO FLIP)
        rgb_surface = pygame.image.tostring(surface, 'RGBA', False)
        width, height = surface.get_size()
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # Upload texture data
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, 
                    GL_RGBA, GL_UNSIGNED_BYTE, rgb_surface)
        
        return texture_id
    
    def _convert_color(self, color: tuple) -> Tuple[float, float, float, float]:
        """Convert color from 0-255 range to 0.0-1.0 range"""
        if len(color) == 3:
            r, g, b = color
            a = 255
        else:
            r, g, b, a = color
        r = max(0, min(255, int(r))) / 255.0
        g = max(0, min(255, int(g))) / 255.0
        b = max(0, min(255, int(b))) / 255.0
        a = max(0, min(255, int(a))) / 255.0
        return (r, g, b, a)
    
    def draw_rect(self, x: int, y: int, width: int, height: int, color: tuple, fill: bool = True, border_width: int = 1):
        """Draw a colored rectangle - PROPER BORDER WITH INSET CONTENT"""
        if not self._initialized or not self.simple_shader.program:
            return
            
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        glUseProgram(self.simple_shader.program)
        glUniform2f(glGetUniformLocation(self.simple_shader.program, "uScreenSize"), 
                float(self.width), float(self.height))
        
        if not fill:
            # Draw border as a filled rectangle (full size)
            glUniform4f(glGetUniformLocation(self.simple_shader.program, "uTransform"), 
                    float(x), float(y), float(width), float(height))
            glUniform4f(glGetUniformLocation(self.simple_shader.program, "uColor"), 
                    r_gl, g_gl, b_gl, a_gl)
            
            glBindVertexArray(self.simple_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
        else:
            # Draw filled rectangle (inset by border width)
            border_w = border_width
            inset_x = x + border_w
            inset_y = y + border_w
            inset_width = width - (2 * border_w)
            inset_height = height - (2 * border_w)
            
            # Only draw if there's space for content
            if inset_width > 0 and inset_height > 0:
                glUniform4f(glGetUniformLocation(self.simple_shader.program, "uTransform"), 
                        float(inset_x), float(inset_y), float(inset_width), float(inset_height))
                glUniform4f(glGetUniformLocation(self.simple_shader.program, "uColor"), 
                        r_gl, g_gl, b_gl, a_gl)
                
                glBindVertexArray(self.simple_shader.vao)
                glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
        
        glUseProgram(0)
    
    def render_surface(self, surface: pygame.Surface, x: int, y: int):
        """Draw a pygame surface as texture"""
        if not self._initialized or not self.texture_shader.program:
            return
            
        width, height = surface.get_size()
        texture_id = self._surface_to_texture(surface)
        
        glUseProgram(self.texture_shader.program)
        
        # Set uniforms
        glUniform2f(glGetUniformLocation(self.texture_shader.program, "uScreenSize"), 
                   float(self.width), float(self.height))
        glUniform4f(glGetUniformLocation(self.texture_shader.program, "uTransform"), 
                   float(x), float(y), float(width), float(height))
        
        # Bind texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glUniform1i(glGetUniformLocation(self.texture_shader.program, "uTexture"), 0)
        
        # Draw
        glBindVertexArray(self.texture_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)
        
        # Clean up texture
        glDeleteTextures(1, [texture_id])
    
    def render_opengl(self):
        """Marker method to identify this as OpenGL renderer"""
        return True
    
    def render_particles(self, particle_data: Dict[str, Any]):
        """Render particles - SUPER OPTIMIZED VERSION"""
        if not self._initialized or particle_data['active_count'] == 0:
            return
        
        active_count = particle_data['active_count']
        
        # OPTIMIZATION: Use single buffer for all particles
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glUseProgram(self.particle_shader.program)
        
        # Constant uniforms
        glUniform2f(glGetUniformLocation(self.particle_shader.program, "uScreenSize"), 
                float(self.width), float(self.height))
        
        glBindVertexArray(self.particle_shader.vao)
        
        # OPTIMIZATION: Batch rendering
        positions = particle_data['positions']
        sizes = particle_data['sizes']
        colors = particle_data['colors']
        alphas = particle_data['alphas']
        
        for i in range(active_count):
            # Combine data into single uniform
            x, y = positions[i, 0], positions[i, 1]
            size = max(2.0, sizes[i])
            alpha = alphas[i] / 255.0
            
            glUniform4f(glGetUniformLocation(self.particle_shader.program, "uParticleData"), 
                    float(x), float(y), float(size), float(alpha))
            
            # Color
            color = colors[i]
            r, g, b = color[0]/255.0, color[1]/255.0, color[2]/255.0
            glUniform4f(glGetUniformLocation(self.particle_shader.program, "uColor"), 
                    r, g, b, 1.0)  # Alpha is handled in shader
            
            glDrawArrays(GL_POINTS, 0, 1)
        
        glBindVertexArray(0)
        glUseProgram(0)