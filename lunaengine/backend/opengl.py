"""
OpenGL-based hardware-accelerated renderer for LunaEngine - DYNAMIC PARTICLE BUFFERS
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
    """Generic shader program for 2D rendering with caching"""
    
    def __init__(self, vertex_source, fragment_source):
        self.program = None
        self.vao = None
        self.vbo = None
        self._uniform_locations = {}
        self._create_shaders(vertex_source, fragment_source)
        if self.program:
            self._setup_geometry()
    
    def _get_uniform_location(self, name):
        """Get cached uniform location"""
        if name not in self._uniform_locations:
            self._uniform_locations[name] = glGetUniformLocation(self.program, name)
        return self._uniform_locations[name]
    
    def _create_shaders(self, vertex_source, fragment_source):
        """Compile shaders with error handling"""
        try:
            vertex_shader = compileShader(vertex_source, GL_VERTEX_SHADER)
            fragment_shader = compileShader(fragment_source, GL_FRAGMENT_SHADER)
            self.program = compileProgram(vertex_shader, fragment_shader)
        except Exception as e:
            print(f"Shader compilation failed: {e}")
            self.program = None

class ParticleShader(ShaderProgram):
    """OPTIMIZED shader for particle rendering with instancing"""
    
    def __init__(self):
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec4 instanceData; // x, y, size, alpha
        layout (location = 2) in vec4 instanceColor; // r, g, b, a
        
        uniform vec2 uScreenSize;
        
        out vec4 vColor;
        out float vAlpha;
        
        void main() {
            // Convert to pixel coordinates
            vec2 pixelPos = aPos * instanceData.z + instanceData.xy;
            
            // Convert to normalized device coordinates
            vec2 ndc = vec2(
                (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
                (1.0 - (pixelPos.y / uScreenSize.y)) * 2.0 - 1.0
            );
            
            gl_Position = vec4(ndc, 0.0, 1.0);
            gl_PointSize = instanceData.z;
            vColor = instanceColor;
            vAlpha = instanceData.w;
        }
        """
        
        fragment_source = """
        #version 330 core
        out vec4 FragColor;
        in vec4 vColor;
        in float vAlpha;
        
        void main() {
            // Create circle shape using distance from center
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            
            // Early discard for performance
            if (dist > 0.5) discard;
            
            // Smooth edges with optimized calculation
            float alpha = 1.0 - smoothstep(0.4, 0.5, dist);
            FragColor = vec4(vColor.rgb, vColor.a * alpha * vAlpha);
        }
        """
        
        super().__init__(vertex_source, fragment_source)
    
    def _setup_geometry(self):
        """Setup instanced particle geometry for maximum performance"""
        # Single point vertex - minimal geometry
        vertices = np.array([0.0, 0.0], dtype=np.float32)
        
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.instance_data_vbo = glGenBuffers(1)  # For position/size/alpha
        self.instance_color_vbo = glGenBuffers(1) # For color data
        
        glBindVertexArray(self.vao)
        
        # Main vertex buffer (static)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Instance data buffer (x, y, size, alpha) - DYNAMIC SIZE
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_data_vbo)
        glBufferData(GL_ARRAY_BUFFER, 1024 * 4 * 4, None, GL_DYNAMIC_DRAW)  # Initial allocation
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribDivisor(1, 1)  # One per instance
        
        # Instance color buffer (r, g, b, a) - DYNAMIC SIZE
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_color_vbo)
        glBufferData(GL_ARRAY_BUFFER, 1024 * 4 * 4, None, GL_DYNAMIC_DRAW)  # Initial allocation
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(2)
        glVertexAttribDivisor(2, 1)  # One per instance
        
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
    
    def _setup_geometry(self):
        """Setup basic quad geometry"""
        vertices = np.array([
            0.0, 0.0,  # bottom-left
            1.0, 0.0,  # bottom-right
            1.0, 1.0,  # top-right
            0.0, 1.0,  # top-left
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
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

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
    
    def _setup_geometry(self):
        """Setup textured quad geometry"""
        vertices = np.array([
            # positions   # texture coords
            0.0, 0.0,    0.0, 0.0,  # bottom-left
            1.0, 0.0,    1.0, 0.0,  # bottom-right  
            1.0, 1.0,    1.0, 1.0,  # top-right
            0.0, 1.0,    0.0, 1.0,  # top-left
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
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

class OpenGLRenderer:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.simple_shader = None
        self.texture_shader = None
        self.particle_shader = None
        self._initialized = False
        
        # Particle optimization with DYNAMIC buffers
        self._max_particles = 1024  # Initial size
        self._particle_instance_data = np.zeros((self._max_particles, 4), dtype=np.float32)
        self._particle_color_data = np.zeros((self._max_particles, 4), dtype=np.float32)
        
    def initialize(self):
        """Initialize OpenGL context and shaders"""
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
        flipped_surface = pygame.transform.flip(surface, False, True)
        rgb_surface = pygame.image.tostring(flipped_surface, 'RGBA', True)
        width, height = surface.get_size()
        
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
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
    
    def _ensure_particle_capacity(self, required_count: int):
        """Ensure particle buffers are large enough - DYNAMIC RESIZING"""
        if required_count <= self._max_particles:
            return
            
        # Calculate new size (next power of two for efficiency)
        new_size = 1
        while new_size < required_count:
            new_size *= 2
        
        print(f"Resizing particle buffers from {self._max_particles} to {new_size}")
        
        # Resize numpy arrays
        self._particle_instance_data = np.zeros((new_size, 4), dtype=np.float32)
        self._particle_color_data = np.zeros((new_size, 4), dtype=np.float32)
        
        # Resize OpenGL buffers
        if self.particle_shader and self.particle_shader.program:
            glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
            glBufferData(GL_ARRAY_BUFFER, new_size * 4 * 4, None, GL_DYNAMIC_DRAW)
            
            glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
            glBufferData(GL_ARRAY_BUFFER, new_size * 4 * 4, None, GL_DYNAMIC_DRAW)
            
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        self._max_particles = new_size
    
    def enable_scissor(self, x: int, y: int, width: int, height: int):
        """Enable scissor test for clipping region"""
        if not self._initialized:
            return
            
        glEnable(GL_SCISSOR_TEST)
        gl_scissor_y = self.height - (y + height)
        glScissor(x, gl_scissor_y, width, height)

    def disable_scissor(self):
        """Disable scissor test"""
        if not self._initialized:
            return
        glDisable(GL_SCISSOR_TEST)
    
    def draw_rect(self, x: int, y: int, width: int, height: int, color: tuple, fill: bool = True, border_width: int = 1):
        """Draw a colored rectangle"""
        if not self._initialized or not self.simple_shader.program:
            return
            
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        glUseProgram(self.simple_shader.program)
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), 
                float(self.width), float(self.height))
        
        if not fill:
            glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 
                    float(x), float(y), float(width), float(height))
            glUniform4f(self.simple_shader._get_uniform_location("uColor"), 
                    r_gl, g_gl, b_gl, a_gl)
            
            glBindVertexArray(self.simple_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
        else:
            border_w = border_width
            inset_x = x + border_w
            inset_y = y + border_w
            inset_width = width - (2 * border_w)
            inset_height = height - (2 * border_w)
            
            if inset_width > 0 and inset_height > 0:
                glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 
                        float(inset_x), float(inset_y), float(inset_width), float(inset_height))
                glUniform4f(self.simple_shader._get_uniform_location("uColor"), 
                        r_gl, g_gl, b_gl, a_gl)
                
                glBindVertexArray(self.simple_shader.vao)
                glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
                glBindVertexArray(0)
        
        glUseProgram(0)
    
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, color: tuple, width: int = 2):
        """Draw a line between two points with specified width"""
        if not self._initialized or not self.simple_shader.program:
            return
            
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        if width <= 1:
            if start_x == end_x:
                x = start_x
                y = min(start_y, end_y)
                height = abs(end_y - start_y)
                self.draw_rect(x, y, 1, height, color, fill=True)
            elif start_y == end_y:
                x = min(start_x, end_x)
                y = start_y
                width_line = abs(end_x - start_x)
                self.draw_rect(x, y, width_line, 1, color, fill=True)
            else:
                self._draw_thick_line_optimized(start_x, start_y, end_x, end_y, color, width)
        else:
            self._draw_thick_line_optimized(start_x, start_y, end_x, end_y, color, width)

    def _draw_thick_line_optimized(self, start_x: int, start_y: int, end_x: int, end_y: int, color: tuple, width: int):
        """Optimized method for drawing thick lines"""
        if start_x == end_x and start_y == end_y:
            return
        
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        dx = end_x - start_x
        dy = end_y - start_y
        length = max(0.1, np.sqrt(dx*dx + dy*dy))
        
        dx /= length
        dy /= length
        
        perp_x = -dy * (width / 2)
        perp_y = dx * (width / 2)
        
        vertices = np.array([
            start_x + perp_x, start_y + perp_y,
            start_x - perp_x, start_y - perp_y,
            end_x - perp_x, end_y - perp_y,
            end_x + perp_x, end_y + perp_y,
        ], dtype=np.float32)
        
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
        
        glUseProgram(self.simple_shader.program)
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), 
                float(self.width), float(self.height))
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), 
                r_gl, g_gl, b_gl, a_gl)
        
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        ebo = glGenBuffers(1)
        
        glBindVertexArray(vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 
                0.0, 0.0, 1.0, 1.0)
        
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        
        glBindVertexArray(0)
        glDeleteVertexArrays(1, [vao])
        glDeleteBuffers(1, [vbo])
        glDeleteBuffers(1, [ebo])
        glUseProgram(0)
        
    def draw_surface(self, surface: pygame.Surface, x: int, y: int):
        """Draw a pygame surface as texture"""
        self.render_surface(surface, x, y)
    
    def render_surface(self, surface: pygame.Surface, x: int, y: int):
        """Draw a pygame surface as texture"""
        if not self._initialized or not self.texture_shader.program:
            return
            
        width, height = surface.get_size()
        texture_id = self._surface_to_texture(surface)
        
        glUseProgram(self.texture_shader.program)
        
        glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), 
                   float(self.width), float(self.height))
        glUniform4f(self.texture_shader._get_uniform_location("uTransform"), 
                   float(x), float(y), float(width), float(height))
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
        
        glBindVertexArray(self.texture_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)
        
        glDeleteTextures(1, [texture_id])
    
    def render_opengl(self):
        """Marker method to identify this as OpenGL renderer"""
        return True
    
    def render_particles(self, particle_data: Dict[str, Any]):
        """HIGHLY OPTIMIZED particle rendering with DYNAMIC BUFFER SIZING"""
        if not self._initialized or particle_data['active_count'] == 0:
            return
        
        active_count = particle_data['active_count']
        
        # CRITICAL FIX: Ensure buffers are large enough
        self._ensure_particle_capacity(active_count)
        
        # OPTIMIZATION: Prepare all particle data in batch using numpy
        positions = particle_data['positions'][:active_count]
        sizes = particle_data['sizes'][:active_count]
        colors = particle_data['colors'][:active_count]
        alphas = particle_data['alphas'][:active_count]
        
        # Batch update instance data - SAFE now with dynamic sizing
        self._particle_instance_data[:active_count, 0] = positions[:, 0]  # x
        self._particle_instance_data[:active_count, 1] = positions[:, 1]  # y  
        self._particle_instance_data[:active_count, 2] = np.maximum(2.0, sizes)  # size
        self._particle_instance_data[:active_count, 3] = alphas / 255.0  # alpha
        
        # Batch update color data - SAFE now with dynamic sizing
        self._particle_color_data[:active_count, 0] = colors[:, 0] / 255.0  # r
        self._particle_color_data[:active_count, 1] = colors[:, 1] / 255.0  # g
        self._particle_color_data[:active_count, 2] = colors[:, 2] / 255.0  # b
        self._particle_color_data[:active_count, 3] = 1.0  # a
        
        # Single OpenGL state setup
        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glUseProgram(self.particle_shader.program)
        
        # Set screen size uniform once
        glUniform2f(self.particle_shader._get_uniform_location("uScreenSize"), 
                float(self.width), float(self.height))
        
        # Upload all instance data in one call
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_data_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, active_count * 4 * 4, self._particle_instance_data)
        
        # Upload all color data in one call  
        glBindBuffer(GL_ARRAY_BUFFER, self.particle_shader.instance_color_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, active_count * 4 * 4, self._particle_color_data)
        
        # SINGLE DRAW CALL for all particles
        glBindVertexArray(self.particle_shader.vao)
        glDrawArraysInstanced(GL_POINTS, 0, 1, active_count)
        glBindVertexArray(0)
        
        glUseProgram(0)