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
    camera_position:pygame.math.Vector2 = pygame.math.Vector2(0, 0)
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
        self.on_max_particles_change:list = [] # Callbacks
        
        # Cache for reusable geometry
        self._circle_cache = {}
        self._polygon_cache = {}
        
    @property
    def max_particles(self) -> int:
        return self._max_particles
    
    @max_particles.setter
    def max_particles(self, value: int):
        if value > self._max_particles:
            for callback in self.on_max_particles_change:
                callback(value)
        self._max_particles = value
        
    @max_particles.getter
    def max_particles(self) -> int:
        return self._max_particles
        
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
        """
        Ensure particle buffers are large enough - DYNAMIC RESIZING
        
        required_count * 1.01 = 101% of current size
        """
        if required_count*1.01 <= self.max_particles:
            return
            
        # Calculate new size (next power of two for efficiency)
        new_size = 1
        while new_size < required_count*1.01:
            new_size *= 2
        
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
        
        self.max_particles = new_size
    
    def enable_scissor(self, x: int, y: int, width: int, height: int):
        """
        Enable scissor test for clipping region.
        
        In OpenGL, the coordinate system has origin at bottom-left,
        while Pygame uses top-left origin. We need to convert coordinates.
        
        Args:
            x (int): X position from left (pygame coordinate system)
            y (int): Y position from top (pygame coordinate system)  
            width (int): Width of scissor region
            height (int): Height of scissor region
        """
        if not self._initialized:
            return
            
        glEnable(GL_SCISSOR_TEST)
        
        gl_scissor_y = self.height - (y + height)
        
        gl_scissor_x = max(0, x)
        gl_scissor_y = max(0, gl_scissor_y)
        gl_scissor_width = min(width, self.width - gl_scissor_x)
        gl_scissor_height = min(height, self.height - gl_scissor_y)
        
        glScissor(gl_scissor_x, gl_scissor_y, gl_scissor_width, gl_scissor_height)

    def disable_scissor(self):
        """Disable scissor test with debugging"""
        if not self._initialized:
            return
            
        glDisable(GL_SCISSOR_TEST)

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
            inset_x = x + border_width
            inset_y = y + border_width
            inset_width = width - (2 * border_width)
            inset_height = height - (2 * border_width)
            
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
        
        # Optimized handling for thin lines
        if width <= 1:
            if start_x == end_x:
                # Vertical line
                x = start_x
                y = min(start_y, end_y)
                height = abs(end_y - start_y)
                self.draw_rect(x, y, 1, height, color, fill=True)
                return
            elif start_y == end_y:
                # Horizontal line
                x = min(start_x, end_x)
                y = start_y
                width_line = abs(end_x - start_x)
                self.draw_rect(x, y, width_line, 1, color, fill=True)
                return
        
        # Use optimized thick line method for all other cases
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
    
    def draw_circle(self, center_x: int, center_y: int, radius: int, color: tuple, fill: bool = True, border_width: int = 1):
        """Draw a circle with specified center, radius and color"""
        if not self._initialized or not self.simple_shader.program:
            return
            
        # Generate circle geometry with caching for performance
        cache_key = (radius, fill, border_width)
        if cache_key in self._circle_cache:
            vao, vbo, ebo, vertex_count = self._circle_cache[cache_key]
        else:
            # Generate circle vertices
            segments = max(16, min(64, radius // 2))  # Adaptive segment count
            
            if fill:
                vertices, indices = self._generate_filled_circle_geometry(segments)
            else:
                vertices, indices = self._generate_hollow_circle_geometry(segments, border_width, radius)
            
            vao, vbo, ebo = self._upload_geometry(vertices, indices)
            vertex_count = len(indices)
            self._circle_cache[cache_key] = (vao, vbo, ebo, vertex_count)
        
        # Render the circle
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        glUseProgram(self.simple_shader.program)
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), 
                float(self.width), float(self.height))
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 
                float(center_x - radius), float(center_y - radius), 
                float(radius * 2), float(radius * 2))
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), 
                r_gl, g_gl, b_gl, a_gl)
        
        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)
    
    def _generate_filled_circle_geometry(self, segments: int):
        """Generate vertices and indices for a filled circle"""
        vertices = [0.0, 0.0]  # Center point
        
        for i in range(int(segments + 1)):
            angle = 2 * np.pi * i / int(segments)
            vertices.extend([np.cos(angle) * 0.5 + 0.5, np.sin(angle) * 0.5 + 0.5])
        
        indices = []
        for i in range(1, int(segments)):
            indices.extend([0, i, i + 1])
        indices.extend([0, int(segments), 1])  # Close the circle
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        
        return vertices, indices
    
    def _generate_hollow_circle_geometry(self, segments: int, border_width: int, radius: int):
        """Generate vertices and indices for a hollow circle (outline)"""
        inner_radius = max(0.1, (radius - border_width) / radius * 0.5)
        outer_radius = 0.5
        
        vertices = []
        # Generate vertices for inner and outer circles
        for i in range(segments + 1):
            angle = 2 * np.pi * i / segments
            # Outer vertex
            vertices.extend([np.cos(angle) * outer_radius + 0.5, np.sin(angle) * outer_radius + 0.5])
            # Inner vertex
            vertices.extend([np.cos(angle) * inner_radius + 0.5, np.sin(angle) * inner_radius + 0.5])
        
        indices = []
        for i in range(segments):
            # Two triangles per segment
            outer_current = i * 2
            inner_current = i * 2 + 1
            outer_next = (i + 1) * 2
            inner_next = (i + 1) * 2 + 1
            
            # First triangle
            indices.extend([outer_current, inner_current, outer_next])
            # Second triangle
            indices.extend([inner_current, inner_next, outer_next])
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        
        return vertices, indices
    
    def draw_polygon(self, points: List[Tuple[int, int]], color: tuple, fill: bool = True, border_width: int = 1):
        """Draw a polygon from a list of points"""
        if not self._initialized or not self.simple_shader.program or len(points) < 3:
            return
            
        # Generate polygon geometry with caching
        cache_key = tuple(points) + (fill, border_width)
        if cache_key in self._polygon_cache:
            vao, vbo, ebo, vertex_count = self._polygon_cache[cache_key]
        else:
            if fill:
                vertices, indices = self._generate_filled_polygon_geometry(points)
            else:
                vertices, indices = self._generate_hollow_polygon_geometry(points, border_width)
            
            vao, vbo, ebo = self._upload_geometry(vertices, indices)
            vertex_count = len(indices)
            self._polygon_cache[cache_key] = (vao, vbo, ebo, vertex_count)
        
        # Calculate bounding box for transform
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        width = max_x - min_x
        height = max_y - min_y
        
        # Render the polygon
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        glUseProgram(self.simple_shader.program)
        glUniform2f(self.simple_shader._get_uniform_location("uScreenSize"), 
                float(self.width), float(self.height))
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 
                float(min_x), float(min_y), float(width), float(height))
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), 
                r_gl, g_gl, b_gl, a_gl)
        
        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)
    
    def _generate_filled_polygon_geometry(self, points: List[Tuple[int, int]]):
        """Generate vertices and indices for a filled polygon using triangle fan"""
        # Normalize points to 0-1 range based on bounding box
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)
        
        vertices = []
        for x, y in points:
            # Normalize to 0-1 range
            norm_x = (x - min_x) / width
            norm_y = (y - min_y) / height
            vertices.extend([norm_x, norm_y])
        
        # Simple triangle fan triangulation (works for convex polygons)
        indices = []
        for i in range(1, len(points) - 1):
            indices.extend([0, i, i + 1])
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        
        return vertices, indices
    
    def _generate_hollow_polygon_geometry(self, points: List[Tuple[int, int]], border_width: int):
        """Generate vertices and indices for a hollow polygon (outline)"""
        # This is a simplified approach - for complex polygons, consider using a library
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)
        
        # Calculate offset for inner polygon
        offset_x = border_width / width
        offset_y = border_width / height
        
        vertices = []
        # Generate outer and inner vertices
        for x, y in points:
            # Outer vertex (original)
            norm_x = (x - min_x) / width
            norm_y = (y - min_y) / height
            vertices.extend([norm_x, norm_y])
            
            # Inner vertex (offset toward center)
            # Simplified approach - for better results, calculate proper inward normals
            center_x = 0.5
            center_y = 0.5
            dir_x = norm_x - center_x
            dir_y = norm_y - center_y
            length = max(0.001, np.sqrt(dir_x*dir_x + dir_y*dir_y))
            dir_x /= length
            dir_y /= length
            
            inner_x = norm_x - dir_x * offset_x
            inner_y = norm_y - dir_y * offset_y
            vertices.extend([inner_x, inner_y])
        
        indices = []
        num_points = len(points)
        for i in range(num_points):
            next_i = (i + 1) % num_points
            
            # Indices for the quad between current and next segment
            outer_current = i * 2
            inner_current = i * 2 + 1
            outer_next = next_i * 2
            inner_next = next_i * 2 + 1
            
            # Two triangles per segment
            indices.extend([outer_current, inner_current, outer_next])
            indices.extend([inner_current, inner_next, outer_next])
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        
        return vertices, indices
    
    def _upload_geometry(self, vertices: np.ndarray, indices: np.ndarray):
        """Upload vertices and indices to GPU, return VAO, VBO, EBO"""
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
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        
        return vao, vbo, ebo
    
    def render_opengl(self, renderer):
        """
        This function is used just for make it detectable in the profiler that is OpenGL.
        
        ! Never Remove it
        """
        return True
        
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
        
        glDeleteTextures([texture_id])
        glUseProgram(0)
    
    def render_particles(self, particle_data: Dict[str, Any]):
        """HIGHLY OPTIMIZED particle rendering with DYNAMIC BUFFER SIZING"""
        if not self._initialized or not particle_data or particle_data['active_count'] == 0:
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
    
    def get_surface(self):
        """
        Get the main screen surface for compatibility with UI elements.
        
        In OpenGL mode, this returns the pygame display surface which can be used
        for fallback rendering when OpenGL is not available for certain operations.
        
        Returns:
            pygame.Surface: The main display surface
        """
        return pygame.display.get_surface()
    
    def cleanup(self):
        """Clean up OpenGL resources"""
        if not self._initialized:
            return
            
        if self.simple_shader and self.simple_shader.program:
            glDeleteProgram(self.simple_shader.program)
        if self.texture_shader and self.texture_shader.program:
            glDeleteProgram(self.texture_shader.program)
        if self.particle_shader and self.particle_shader.program:
            glDeleteProgram(self.particle_shader.program)
        
        # Clean up cached geometry
        for vao, vbo, ebo, _ in self._circle_cache.values():
            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
            glDeleteBuffers(1, [ebo])
        
        for vao, vbo, ebo, _ in self._polygon_cache.values():
            glDeleteVertexArrays(1, [vao])
            glDeleteBuffers(1, [vbo])
            glDeleteBuffers(1, [ebo])
        
        self._circle_cache.clear()
        self._polygon_cache.clear()
        
        self._initialized = False