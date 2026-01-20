"""
lunaengine/backend/opengl.py

OpenGL-based hardware-accelerated renderer for LunaEngine - DYNAMIC PARTICLE BUFFERS & FILTER SYSTEM
"""

import pygame
import numpy as np
from typing import Tuple, Dict, Any, List, TYPE_CHECKING, Optional
from enum import Enum

# Check if OpenGL is available
try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("OpenGL not available - falling back to software rendering")
    
if TYPE_CHECKING:
    from ..graphics import Camera

# ============================================================================
# FILTER SYSTEM ENUMS
# ============================================================================

class FilterType(Enum):
    """Enumeration of available filter types"""
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
    """Enumeration of filter region shapes"""
    FULLSCREEN = "fullscreen"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"

# ============================================================================
# FILTER CLASS
# ============================================================================

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
# SHADER CLASSES
# ============================================================================

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

class FilterShader(ShaderProgram):
    """Shader for applying post-processing filters"""
    
    def __init__(self):
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        
        out vec2 TexCoord;
        
        void main() {
            gl_Position = vec4(aPos, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        
        fragment_source = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        
        uniform sampler2D screenTexture;
        uniform vec2 screenSize;
        uniform float time;
        
        // Filter parameters
        uniform int filterType;
        uniform float intensity;
        uniform vec4 regionParams; // x, y, width, height
        uniform float radius;
        uniform float feather;
        uniform int regionType; // 0=full, 1=rect, 2=circle
        
        // Common utility functions
        float luminance(vec3 color) {
            return dot(color, vec3(0.299, 0.587, 0.114));
        }
        
        vec3 rgb2hsv(vec3 c) {
            vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
            vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
            vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
            
            float d = q.x - min(q.w, q.y);
            float e = 1.0e-10;
            return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
        }
        
        vec3 hsv2rgb(vec3 c) {
            vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
            vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
            return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
        }
        
        // Region masking
        float getRegionMask(vec2 pixelCoord) {
            if (regionType == 0) return 1.0; // Fullscreen
            
            if (regionType == 1) { // Rectangle
                vec2 rectMin = regionParams.xy;
                vec2 rectMax = regionParams.xy + regionParams.zw;
                
                // Distance to rectangle edges
                vec2 dist = vec2(
                    max(rectMin.x - pixelCoord.x, pixelCoord.x - rectMax.x),
                    max(rectMin.y - pixelCoord.y, pixelCoord.y - rectMax.y)
                );
                
                float edgeDist = max(dist.x, dist.y);
                return 1.0 - smoothstep(0.0, feather, edgeDist);
            }
            else { // Circle (regionType == 2)
                vec2 center = regionParams.xy + regionParams.zw * 0.5;
                float dist = distance(pixelCoord, center);
                float effectiveRadius = min(regionParams.z, regionParams.w) * 0.5 * radius;
                return 1.0 - smoothstep(effectiveRadius - feather, effectiveRadius + feather, dist);
            }
        }
        
        // FILTER FUNCTIONS - READY TO USE
        
        // 1. VIGNETTE FILTER (darkens edges)
        vec3 applyVignette(vec3 color, vec2 uv) {
            vec2 center = uv - 0.5;
            float dist = length(center);
            float vignette = 1.0 - dist * 2.0 * intensity;
            vignette = smoothstep(0.0, 0.8, vignette);
            return color * vignette;
        }
        
        // 2. GAUSSIAN BLUR FILTER
        vec3 applyBlur(vec3 color) {
            vec2 texelSize = 1.0 / screenSize;
            vec3 result = vec3(0.0);
            float total = 0.0;
            
            // 5x5 Gaussian blur
            float kernel[25] = float[25](
                1.0, 4.0, 7.0, 4.0, 1.0,
                4.0, 16.0, 26.0, 16.0, 4.0,
                7.0, 26.0, 41.0, 26.0, 7.0,
                4.0, 16.0, 26.0, 16.0, 4.0,
                1.0, 4.0, 7.0, 4.0, 1.0
            );
            
            int idx = 0;
            for (int y = -2; y <= 2; y++) {
                for (int x = -2; x <= 2; x++) {
                    vec2 offset = vec2(x, y) * texelSize * 2.0;
                    result += texture(screenTexture, TexCoord + offset).rgb * kernel[idx];
                    total += kernel[idx];
                    idx++;
                }
            }
            
            return result / total;
        }
        
        // 3. SEPIA FILTER (old photo effect)
        vec3 applySepia(vec3 color) {
            vec3 sepia = vec3(
                dot(color, vec3(0.393, 0.769, 0.189)),
                dot(color, vec3(0.349, 0.686, 0.168)),
                dot(color, vec3(0.272, 0.534, 0.131))
            );
            return mix(color, sepia, intensity);
        }
        
        // 4. GRAYSCALE FILTER (black and white)
        vec3 applyGrayscale(vec3 color) {
            float gray = luminance(color);
            return mix(color, vec3(gray), intensity);
        }
        
        // 5. INVERT FILTER (color inversion)
        vec3 applyInvert(vec3 color) {
            vec3 inverted = vec3(1.0) - color;
            return mix(color, inverted, intensity);
        }
        
        // 6. WARM TEMPERATURE FILTER
        vec3 applyWarmTemperature(vec3 color) {
            vec3 warm = vec3(1.0, 0.9, 0.7);
            return mix(color, color * warm, intensity);
        }
        
        // 7. COLD TEMPERATURE FILTER
        vec3 applyColdTemperature(vec3 color) {
            vec3 cold = vec3(0.7, 0.9, 1.0);
            return mix(color, color * cold, intensity);
        }
        
        // 8. NIGHT VISION FILTER (green night vision)
        vec3 applyNightVision(vec3 color) {
            float green = luminance(color) * 1.5;
            float scanLine = sin(TexCoord.y * screenSize.y * 0.7 + time * 5.0) * 0.1 + 0.9;
            float noise = fract(sin(dot(TexCoord, vec2(12.9898, 78.233))) * 43758.5453) * 0.1;
            vec3 nightColor = vec3(0.0, green * scanLine + noise, 0.0);
            return mix(color, nightColor, intensity);
        }
        
        // 9. CRT FILTER (old monitor effect)
        vec3 applyCRT(vec3 color) {
            // Scanlines
            float scanline = sin(TexCoord.y * screenSize.y * 0.7) * 0.04 + 0.96;
            
            // Vignette
            vec2 uv = TexCoord - 0.5;
            float vignette = 1.0 - length(uv) * 0.7;
            
            // Color bleed (simple RGB separation)
            float offset = 0.003;
            vec3 bleed;
            bleed.r = texture(screenTexture, TexCoord + vec2(offset, 0.0)).r;
            bleed.g = texture(screenTexture, TexCoord).g;
            bleed.b = texture(screenTexture, TexCoord - vec2(offset, 0.0)).b;
            
            // Curvature
            uv *= 1.2;
            uv = uv * (1.0 + length(uv) * 0.2);
            
            vec3 crtColor = bleed * scanline * vignette;
            return mix(color, crtColor, intensity);
        }
        
        // 10. PIXELATE FILTER
        vec3 applyPixelate(vec3 color) {
            float pixelSize = 8.0 + (1.0 - intensity) * 15.0;
            vec2 pixelCoord = floor(TexCoord * screenSize / pixelSize) * pixelSize / screenSize;
            vec3 pixelated = texture(screenTexture, pixelCoord).rgb;
            return mix(color, pixelated, intensity);
        }
        
        // 11. BLOOM FILTER (glow effect)
        vec3 applyBloom(vec3 color) {
            vec2 texelSize = 1.0 / screenSize;
            vec3 blur = vec3(0.0);
            int samples = 5;
            float total = 0.0;
            
            for (int i = -samples; i <= samples; i++) {
                for (int j = -samples; j <= samples; j++) {
                    float weight = 1.0 / (1.0 + abs(float(i)) + abs(float(j)));
                    vec2 offset = vec2(i, j) * texelSize * 2.0;
                    blur += texture(screenTexture, TexCoord + offset).rgb * weight;
                    total += weight;
                }
            }
            
            blur /= total;
            
            // Only apply to bright areas
            float brightness = luminance(color);
            float glow = smoothstep(0.7, 1.0, brightness);
            
            return mix(color, mix(color, blur, glow * 0.5), intensity);
        }
        
        // 12. EDGE DETECTION FILTER
        vec3 applyEdgeDetect(vec3 color) {
            vec2 texelSize = 1.0 / screenSize;
            
            // Sobel edge detection
            float gx[9] = float[9](-1.0, 0.0, 1.0, -2.0, 0.0, 2.0, -1.0, 0.0, 1.0);
            float gy[9] = float[9](-1.0, -2.0, -1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 1.0);
            
            float sx = 0.0;
            float sy = 0.0;
            int idx = 0;
            
            for (int y = -1; y <= 1; y++) {
                for (int x = -1; x <= 1; x++) {
                    vec2 offset = vec2(x, y) * texelSize;
                    float sample = luminance(texture(screenTexture, TexCoord + offset).rgb);
                    
                    sx += sample * gx[idx];
                    sy += sample * gy[idx];
                    idx++;
                }
            }
            
            float edge = sqrt(sx * sx + sy * sy);
            vec3 edgeColor = vec3(edge > 0.2 ? 1.0 : 0.0);
            return mix(color, edgeColor, intensity);
        }
        
        // 13. EMBOSS FILTER
        vec3 applyEmboss(vec3 color) {
            vec2 texelSize = 1.0 / screenSize;
            
            float sample1 = luminance(texture(screenTexture, TexCoord + vec2(-texelSize.x, -texelSize.y)).rgb);
            float sample2 = luminance(texture(screenTexture, TexCoord + vec2(texelSize.x, texelSize.y)).rgb);
            
            float emboss = sample2 - sample1 + 0.5;
            vec3 embossColor = vec3(emboss);
            return mix(color, embossColor, intensity);
        }
        
        // 14. SHARPEN FILTER
        vec3 applySharpen(vec3 color) {
            vec2 texelSize = 1.0 / screenSize;
            
            // Unsharp masking (sharp = original + (original - blurred))
            vec3 blur = (texture(screenTexture, TexCoord + vec2(-texelSize.x, 0.0)).rgb +
                        texture(screenTexture, TexCoord + vec2(texelSize.x, 0.0)).rgb +
                        texture(screenTexture, TexCoord + vec2(0.0, -texelSize.y)).rgb +
                        texture(screenTexture, TexCoord + vec2(0.0, texelSize.y)).rgb) * 0.25;
            
            vec3 sharp = color + (color - blur) * 2.0 * intensity;
            vec3 sharpened = clamp(sharp, 0.0, 1.0);
            return mix(color, sharpened, intensity);
        }
        
        // 15. POSTERIZE FILTER
        vec3 applyPosterize(vec3 color) {
            float levels = 4.0 + (1.0 - intensity) * 12.0;
            vec3 posterized = floor(color * levels) / levels;
            return mix(color, posterized, intensity);
        }
        
        // 16. NEON FILTER (glowing edges)
        vec3 applyNeon(vec3 color) {
            vec2 texelSize = 1.0 / screenSize;
            
            // Sobel for edge detection
            float gx[9] = float[9](-1.0, 0.0, 1.0, -2.0, 0.0, 2.0, -1.0, 0.0, 1.0);
            float gy[9] = float[9](-1.0, -2.0, -1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 1.0);
            
            vec3 sx = vec3(0.0);
            vec3 sy = vec3(0.0);
            int idx = 0;
            
            for (int y = -1; y <= 1; y++) {
                for (int x = -1; x <= 1; x++) {
                    vec2 offset = vec2(x, y) * texelSize;
                    vec3 sample = texture(screenTexture, TexCoord + offset).rgb;
                    
                    sx += sample * gx[idx];
                    sy += sample * gy[idx];
                    idx++;
                }
            }
            
            vec3 edge = sqrt(sx * sx + sy * sy);
            vec3 neon = edge * 3.0 * intensity;
            
            // Add color to neon based on original color hue
            vec3 hsv = rgb2hsv(color);
            hsv.y = 1.0; // Full saturation for neon
            hsv.z = 1.0; // Full value
            vec3 neonColor = hsv2rgb(hsv) * neon;
            
            return mix(color, color + neonColor, intensity);
        }
        
        // 17. RADIAL BLUR FILTER (zoom blur)
        vec3 applyRadialBlur(vec3 color) {
            vec2 center = vec2(0.5, 0.5);
            vec2 uv = TexCoord - center;
            float dist = length(uv);
            
            vec3 result = vec3(0.0);
            float samples = 10.0 * intensity;
            float total = 0.0;
            
            for (float i = 0.0; i < samples; i++) {
                float percent = i / samples;
                float weight = 1.0 - percent;
                vec2 sampleUV = center + uv * (1.0 - percent * 0.5);
                result += texture(screenTexture, sampleUV).rgb * weight;
                total += weight;
            }
            
            return result / total;
        }
        
        // 18. FISHEYE FILTER
        vec3 applyFisheye(vec3 color) {
            vec2 center = vec2(0.5, 0.5);
            vec2 uv = TexCoord - center;
            float dist = length(uv);
            
            float strength = 0.5 * intensity;
            vec2 distorted = uv * (1.0 - strength * dist * dist);
            vec2 sampleUV = center + distorted;
            
            if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
                return color;
            }
            
            return texture(screenTexture, sampleUV).rgb;
        }
        
        // 19. TWIRL FILTER
        vec3 applyTwirl(vec3 color) {
            vec2 center = vec2(0.5, 0.5);
            vec2 uv = TexCoord - center;
            float angle = length(uv) * 3.0 * intensity;
            
            float cosAngle = cos(angle);
            float sinAngle = sin(angle);
            vec2 twisted = vec2(
                uv.x * cosAngle - uv.y * sinAngle,
                uv.x * sinAngle + uv.y * cosAngle
            );
            
            vec2 sampleUV = center + twisted;
            
            if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
                return color;
            }
            
            return texture(screenTexture, sampleUV).rgb;
        }
        
        // MAIN FILTER SWITCH
        vec3 applyFilter(vec3 color, int type) {
            switch(type) {
                case 1: return applyVignette(color, TexCoord);
                case 2: return applyBlur(color);
                case 3: return applySepia(color);
                case 4: return applyGrayscale(color);
                case 5: return applyInvert(color);
                case 6: return applyWarmTemperature(color);
                case 7: return applyColdTemperature(color);
                case 8: return applyNightVision(color);
                case 9: return applyCRT(color);
                case 10: return applyPixelate(color);
                case 11: return applyBloom(color);
                case 12: return applyEdgeDetect(color);
                case 13: return applyEmboss(color);
                case 14: return applySharpen(color);
                case 15: return applyPosterize(color);
                case 16: return applyNeon(color);
                case 17: return applyRadialBlur(color);
                case 18: return applyFisheye(color);
                case 19: return applyTwirl(color);
                default: return color;
            }
        }
        
        void main() {
            vec4 original = texture(screenTexture, TexCoord);
            vec3 color = original.rgb;
            
            // Get current pixel coordinate
            vec2 pixelCoord = gl_FragCoord.xy;
            
            // Get region mask
            float regionMask = getRegionMask(pixelCoord);
            
            if (regionMask > 0.0 && filterType != 0) {
                // Apply the selected filter
                vec3 filtered = applyFilter(color, filterType);
                
                // Blend with original based on intensity and region mask
                color = mix(color, filtered, intensity * regionMask);
            }
            
            FragColor = vec4(color, original.a);
        }
        """
        
        super().__init__(vertex_source, fragment_source)
    
    def _setup_geometry(self):
        """Setup fullscreen quad for filter rendering"""
        vertices = np.array([
            # positions   # texture coords
            -1.0,  1.0,  0.0, 1.0,  # top-left
            -1.0, -1.0,  0.0, 0.0,  # bottom-left
             1.0, -1.0,  1.0, 0.0,  # bottom-right
             1.0,  1.0,  1.0, 1.0,  # top-right
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

class RoundedRectShader(ShaderProgram):
    """Shader for drawing rectangles with per-corner rounded corners"""
    
    def __init__(self):
        vertex_source = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        
        out vec2 vPos;
        uniform vec2 uScreenSize;
        uniform vec4 uTransform; // x, y, width, height
        uniform float uFeather; // Edge smoothness
        
        void main() {
            // Convert to pixel coordinates
            vec2 pixelPos = aPos * uTransform.zw + uTransform.xy;
            
            // Convert to normalized device coordinates
            vec2 ndc = vec2(
                (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
                (1.0 - (pixelPos.y / uScreenSize.y)) * 2.0 - 1.0
            );
            
            gl_Position = vec4(ndc, 0.0, 1.0);
            vPos = aPos;
        }
        """
        
        fragment_source = """
        #version 330 core
        out vec4 FragColor;
        in vec2 vPos;
        
        uniform vec4 uColor;
        uniform vec4 uCornerRadii; // top-left, top-right, bottom-right, bottom-left
        uniform float uFeather;
        uniform vec2 uRectSize;
        uniform int uFill; // 1 = filled, 0 = outline
        uniform float uBorderWidth;
        
        // Helper function for individual corner rounded box SDF
        float roundedBoxSDF(vec2 p, vec2 b, vec4 r) {
            // For each corner, we calculate distance and use max(0, r_i - distance) for rounding
            // This is a simplified approach that works well for UI elements
            
            // Get distances to each edge
            vec2 q = abs(p);
            
            // Calculate distance to each corner's circle
            // Top-left (r.x)
            vec2 tlCorner = q - b + vec2(r.x, r.x);
            float tlDist = length(max(tlCorner, 0.0)) + min(max(tlCorner.x, tlCorner.y), 0.0) - r.x;
            
            // Top-right (r.y)
            vec2 trCorner = q - vec2(b.x - r.y, b.y - r.y);
            float trDist = length(max(trCorner, 0.0)) + min(max(trCorner.x, trCorner.y), 0.0) - r.y;
            
            // Bottom-right (r.z)
            vec2 brCorner = q - b + vec2(r.z, r.z);
            float brDist = length(max(brCorner, 0.0)) + min(max(brCorner.x, brCorner.y), 0.0) - r.z;
            
            // Bottom-left (r.w)
            vec2 blCorner = q - vec2(b.x - r.w, b.y - r.w);
            float blDist = length(max(blCorner, 0.0)) + min(max(blCorner.x, blCorner.y), 0.0) - r.w;
            
            // Determine which corner region we're in
            // Top-left quadrant
            if (p.x < 0.0 && p.y > 0.0) return tlDist;
            // Top-right quadrant
            else if (p.x >= 0.0 && p.y > 0.0) return trDist;
            // Bottom-right quadrant
            else if (p.x >= 0.0 && p.y <= 0.0) return brDist;
            // Bottom-left quadrant
            else return blDist;
        }
        
        // Alternative: Better SDF that handles per-corner radii
        float roundedRectSDF(vec2 p, vec2 b, vec4 r) {
            r.xy = (p.x > 0.0) ? r.yw : r.xz;
            r.x  = (p.y > 0.0) ? r.x : r.y;
            
            vec2 q = abs(p) - b + r.x;
            return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r.x;
        }
        
        void main() {
            // Convert to pixel space
            vec2 pixelPos = vPos * uRectSize;
            
            // Center coordinate system (0,0 at center of rectangle)
            vec2 center = uRectSize * 0.5;
            vec2 centeredPos = pixelPos - center;
            
            // Half size (without considering radii yet)
            vec2 halfSize = center;
            
            // Calculate signed distance to rounded rectangle
            float distance = roundedRectSDF(centeredPos, halfSize, uCornerRadii);
            
            if (uFill == 1) {
                // Filled rectangle with smooth edges
                float alpha = 1.0 - smoothstep(-uFeather, uFeather, distance);
                if (alpha <= 0.0) discard;
                FragColor = vec4(uColor.rgb, uColor.a * alpha);
            } else {
                // Outline only
                float borderOuter = smoothstep(-uFeather, uFeather, distance);
                float borderInner = smoothstep(-uFeather, uFeather, distance + uBorderWidth);
                float alpha = borderOuter - borderInner;
                if (alpha <= 0.0) discard;
                FragColor = vec4(uColor.rgb, uColor.a * alpha);
            }
        }
        """
        
        super().__init__(vertex_source, fragment_source)
    
    def _setup_geometry(self):
        """Setup quad geometry for rectangle"""
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

# ============================================================================
# MAIN OPENGL RENDERER WITH FILTER SYSTEM
# ============================================================================

class OpenGLRenderer:
    camera_position: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.simple_shader = None
        self.texture_shader = None
        self.particle_shader = None
        self.filter_shader = None
        self.rounded_rect_shader = None
        self._initialized = False
        
        # Particle optimization with DYNAMIC buffers
        self._max_particles = 1024
        self._particle_instance_data = np.zeros((self._max_particles, 4), dtype=np.float32)
        self._particle_color_data = np.zeros((self._max_particles, 4), dtype=np.float32)
        self.on_max_particles_change: list = [] # Callbacks
        
        self.filters: List[Filter] = []
        self._filter_framebuffer = None
        self._filter_texture = None
        self._filter_renderbuffer = None
        
        # Cache for reusable geometry
        self._circle_cache = {}
        self._polygon_cache = {}
        
        # Current render target
        self._current_target = None
        
    @property
    def max_particles(self) -> int:
        return self._max_particles
    
    @max_particles.setter
    def max_particles(self, value: int):
        if value > self._max_particles:
            for callback in self.on_max_particles_change:
                callback(value)
        self._max_particles = value
        
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
    
    def _initialize_filter_framebuffer(self):
        """Initialize framebuffer for filter rendering"""
        try:
            # Create framebuffer
            self._filter_framebuffer = glGenFramebuffers(1)
            self._filter_texture = glGenTextures(1)
            self._filter_renderbuffer = glGenRenderbuffers(1)
            
            # Setup texture
            glBindTexture(GL_TEXTURE_2D, self._filter_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 
                        0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            
            # Setup renderbuffer
            glBindRenderbuffer(GL_RENDERBUFFER, self._filter_renderbuffer)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, self.width, self.height)
            
            # Attach to framebuffer
            glBindFramebuffer(GL_FRAMEBUFFER, self._filter_framebuffer)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._filter_texture, 0)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, 
                                    GL_RENDERBUFFER, self._filter_renderbuffer)
            
            # Check framebuffer status
            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                print("Filter framebuffer is not complete!")
                return False
            
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            return True
            
        except Exception as e:
            print(f"Failed to initialize filter framebuffer: {e}")
            return False
    
    # ========================================================================
    # FILTER SYSTEM METHODS - SIMPLE AND DIRECT
    # ========================================================================
    
    def add_filter(self, filter_obj: Filter):
        """
        Add a filter to be applied during rendering.
        
        Args:
            filter_obj: Filter object with settings
        """
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj: Filter):
        """
        Remove a filter.
        
        Args:
            filter_obj: Filter object to remove
        """
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
    
    def clear_filters(self):
        """Remove all filters"""
        self.filters.clear()
    
    def create_quick_filter(self, 
                          filter_type: FilterType, 
                          intensity: float = 1.0,
                          x: float = 0, y: float = 0,
                          width: float = None, height: float = None,
                          radius: float = 50.0,
                          feather: float = 10.0) -> Filter:
        """
        Quick helper to create and add a filter in one call.
        
        Args:
            filter_type: Type of filter
            intensity: Filter strength (0.0 to 1.0)
            x, y: Position (top-left for rect, center for circle)
            width, height: Size (defaults to screen size)
            radius: Radius for circular regions
            feather: Edge softness
            
        Returns:
            Filter: Created filter object
        """
        if width is None or height is None:
            width, height = self.width, self.height
        
        region_type = FilterRegionType.FULLSCREEN
        if width < self.width or height < self.height:
            region_type = FilterRegionType.RECTANGLE
        if filter_type in [FilterType.VIGNETTE, FilterType.CRT]:
            region_type = FilterRegionType.FULLSCREEN  # These are usually fullscreen
        
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
    
    # QUICK FILTER FUNCTIONS - READY TO USE
    
    def apply_vignette(self, intensity: float = 0.7, feather: float = 100.0) -> Filter:
        """Quick vignette filter (darkens edges)"""
        return self.create_quick_filter(
            filter_type=FilterType.VIGNETTE,
            intensity=intensity,
            feather=feather
        )
    
    def apply_blur(self, intensity: float = 0.5, x: float = 0, y: float = 0, 
                  width: float = None, height: float = None) -> Filter:
        """Quick blur filter"""
        return self.create_quick_filter(
            filter_type=FilterType.BLUR,
            intensity=intensity,
            x=x, y=y,
            width=width, height=height,
            feather=20.0
        )
    
    def apply_sepia(self, intensity: float = 1.0) -> Filter:
        """Quick sepia (old photo) filter"""
        return self.create_quick_filter(
            filter_type=FilterType.SEPIA,
            intensity=intensity
        )
    
    def apply_grayscale(self, intensity: float = 1.0) -> Filter:
        """Quick black and white filter"""
        return self.create_quick_filter(
            filter_type=FilterType.GRAYSCALE,
            intensity=intensity
        )
    
    def apply_invert(self, intensity: float = 1.0) -> Filter:
        """Quick color inversion filter"""
        return self.create_quick_filter(
            filter_type=FilterType.INVERT,
            intensity=intensity
        )
    
    def apply_warm_temperature(self, intensity: float = 0.5) -> Filter:
        """Quick warm temperature filter"""
        return self.create_quick_filter(
            filter_type=FilterType.TEMPERATURE_WARM,
            intensity=intensity
        )
    
    def apply_cold_temperature(self, intensity: float = 0.5) -> Filter:
        """Quick cold temperature filter"""
        return self.create_quick_filter(
            filter_type=FilterType.TEMPERATURE_COLD,
            intensity=intensity
        )
    
    def apply_night_vision(self, intensity: float = 0.9) -> Filter:
        """Quick night vision (green) effect"""
        return self.create_quick_filter(
            filter_type=FilterType.NIGHT_VISION,
            intensity=intensity
        )
    
    def apply_crt_effect(self, intensity: float = 0.8) -> Filter:
        """Quick CRT (old monitor) effect"""
        return self.create_quick_filter(
            filter_type=FilterType.CRT,
            intensity=intensity
        )
    
    def apply_pixelate(self, intensity: float = 0.7) -> Filter:
        """Quick pixelation effect"""
        return self.create_quick_filter(
            filter_type=FilterType.PIXELATE,
            intensity=intensity
        )
    
    def apply_bloom(self, intensity: float = 0.5) -> Filter:
        """Quick bloom (glow) effect"""
        return self.create_quick_filter(
            filter_type=FilterType.BLOOM,
            intensity=intensity
        )
    
    def apply_edge_detect(self, intensity: float = 0.8) -> Filter:
        """Quick edge detection filter"""
        return self.create_quick_filter(
            filter_type=FilterType.EDGE_DETECT,
            intensity=intensity
        )
    
    def apply_emboss(self, intensity: float = 0.7) -> Filter:
        """Quick emboss effect"""
        return self.create_quick_filter(
            filter_type=FilterType.EMBOSS,
            intensity=intensity
        )
    
    def apply_sharpen(self, intensity: float = 0.5) -> Filter:
        """Quick sharpen filter"""
        return self.create_quick_filter(
            filter_type=FilterType.SHARPEN,
            intensity=intensity
        )
    
    def apply_posterize(self, intensity: float = 0.6) -> Filter:
        """Quick posterize effect"""
        return self.create_quick_filter(
            filter_type=FilterType.POSTERIZE,
            intensity=intensity
        )
    
    def apply_neon(self, intensity: float = 0.7) -> Filter:
        """Quick neon glow effect"""
        return self.create_quick_filter(
            filter_type=FilterType.NEON,
            intensity=intensity
        )
    
    def apply_radial_blur(self, intensity: float = 0.5) -> Filter:
        """Quick radial blur (zoom effect)"""
        return self.create_quick_filter(
            filter_type=FilterType.RADIAL_BLUR,
            intensity=intensity
        )
    
    def apply_fisheye(self, intensity: float = 0.4) -> Filter:
        """Quick fisheye lens effect"""
        return self.create_quick_filter(
            filter_type=FilterType.FISHEYE,
            intensity=intensity
        )
    
    def apply_twirl(self, intensity: float = 0.3) -> Filter:
        """Quick twirl distortion effect"""
        return self.create_quick_filter(
            filter_type=FilterType.TWIRL,
            intensity=intensity
        )
    
    def apply_circular_grayscale(self, center_x: float, center_y: float, 
                               radius: float = 100.0, intensity: float = 1.0) -> Filter:
        """
        Apply grayscale filter to a circular region.
        
        Args:
            center_x: X position of circle center
            center_y: Y position of circle center
            radius: Radius of the circle
            intensity: Filter strength
            
        Returns:
            Filter: Created filter
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
    
    def apply_rectangular_blur(self, x: float, y: float, 
                             width: float, height: float, 
                             intensity: float = 0.5) -> Filter:
        """
        Apply blur filter to a rectangular region.
        
        Args:
            x, y: Top-left position
            width, height: Size of rectangle
            intensity: Blur strength
            
        Returns:
            Filter: Created filter
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
    # FRAME RENDERING WITH FILTER SUPPORT
    # ========================================================================
    
    def begin_frame(self):
        """Begin rendering frame"""
        if not self._initialized:
            return
        
        # If we have filters, render to filter framebuffer
        if self.filters:
            glBindFramebuffer(GL_FRAMEBUFFER, self._filter_framebuffer)
            glViewport(0, 0, self.width, self.height)
        
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    def end_frame(self):
        """End rendering frame - apply filters if any"""
        if not self._initialized:
            return
        
        # Apply filters if we have any
        if self.filters:
            # Switch to default framebuffer
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glViewport(0, 0, self.width, self.height)
            
            # Apply all filters
            self._apply_filters()
        
        pygame.display.flip()
    
    def _apply_filters(self):
        """Apply all registered filters to the screen"""
        if not self.filters or not self.filter_shader.program:
            return
        
        # Update filter animations
        for filter_obj in self.filters:
            if filter_obj.enabled:
                filter_obj.update(1.0/60.0)  # Approximate delta time
        
        # Use filter shader
        glUseProgram(self.filter_shader.program)
        
        # Bind the filter texture (what we just rendered)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._filter_texture)
        glUniform1i(self.filter_shader._get_uniform_location("screenTexture"), 0)
        
        # Set screen size
        glUniform2f(self.filter_shader._get_uniform_location("screenSize"), 
                   float(self.width), float(self.height))
        
        # Apply filters one by one (they stack)
        for filter_obj in self.filters:
            if not filter_obj.enabled:
                continue
            
            # Set filter type
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
            
            filter_id = filter_type_map.get(filter_obj.filter_type, 0)
            glUniform1i(self.filter_shader._get_uniform_location("filterType"), filter_id)
            
            # Set filter intensity
            glUniform1f(self.filter_shader._get_uniform_location("intensity"), 
                       filter_obj.intensity)
            
            # Set time for animated filters
            glUniform1f(self.filter_shader._get_uniform_location("time"), 
                       filter_obj.time)
            
            # Set region parameters
            region_type_map = {
                FilterRegionType.FULLSCREEN: 0,
                FilterRegionType.RECTANGLE: 1,
                FilterRegionType.CIRCLE: 2,
            }
            
            glUniform1i(self.filter_shader._get_uniform_location("regionType"), 
                       region_type_map.get(filter_obj.region_type, 0))
            
            glUniform4f(self.filter_shader._get_uniform_location("regionParams"),
                       filter_obj.region_pos[0], filter_obj.region_pos[1],
                       filter_obj.region_size[0], filter_obj.region_size[1])
            
            glUniform1f(self.filter_shader._get_uniform_location("radius"), 
                       filter_obj.radius)
            glUniform1f(self.filter_shader._get_uniform_location("feather"), 
                       filter_obj.feather)
            
            # Draw fullscreen quad with filter
            glBindVertexArray(self.filter_shader.vao)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        
        glBindVertexArray(0)
        glUseProgram(0)
    
    # ========================================================================
    # EXISTING RENDERER METHODS (remain unchanged)
    # ========================================================================
    
    def get_surface(self) -> pygame.Surface:
        """
        Get the main screen surface for compatibility with UI elements.
        
        Returns:
            pygame.Surface: The main display surface
        """
        return pygame.display.get_surface()
    
    def set_surface(self, surface: pygame.Surface):
        """
        Set custom surface for rendering using Framebuffer Objects.
        
        Args:
            surface: Pygame surface to use as render target
        """
        if surface == self._current_target:
            return
        if surface is None: # Is None, then return to default framebuffer
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            self.width, self.height = self.get_surface().get_size()
        else:
            texture_id = self._surface_to_texture(surface)
            fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture_id, 0)
            
            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                print("Framebuffer not complete!")
                glBindFramebuffer(GL_FRAMEBUFFER, 0)
                return
            
            self.width, self.height = surface.get_size()
            
        self._current_target = surface
    
    def _surface_to_texture(self, surface: pygame.Surface) -> int:
        """
        Convert pygame surface to OpenGL texture with proper color format.
        
        Args:
            surface: Pygame surface to convert
            
        Returns:
            int: OpenGL texture ID
        """
        # Ensure surface has correct format for OpenGL
        if surface.get_bytesize() != 4 or not (surface.get_flags() & pygame.SRCALPHA):
            # Convert to RGBA format with alpha channel
            converted_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA, 32)
            converted_surface.blit(surface, (0, 0))
            surface = converted_surface
        
        # Get surface dimensions
        width, height = surface.get_size()
        
        # Convert surface to string in RGBA format
        # IMPORTANT: No flip here - let the shader handle coordinates correctly
        image_data = pygame.image.tostring(surface, 'RGBA', False)
        
        # Generate and bind texture
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        # Upload texture data
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, 
                    GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        
        # Generate mipmaps for better quality
        glGenerateMipmap(GL_TEXTURE_2D)
        
        return texture_id
    
    def _convert_color(self, color: Tuple[int, int, int, float]) -> Tuple[float, float, float, float]:
        """
        Convert color tuple to normalized RGBA values
        
        R(0-255) -> R(0.0-1.0)
        
        B(0-255) -> B(0.0-1.0)
        
        G(0-255) -> G(0.0-1.0)
        
        A(0.0-1.0) -> A(0.0-1.0)
        """
        if color:
            if len(color) == 3:
                r, g, b = color
                a = 1.0
            else:
                r, g, b, a = color
            
            # Add compatibility with older engine version wich used 0~255
            if a > 1.0:
                a = a / 255
            if a < 0.0:
                a = 0.0
            r = max(0, min(255, int(r))) / 255.0
            g = max(0, min(255, int(g))) / 255.0
            b = max(0, min(255, int(b))) / 255.0
            return (r, g, b, a)
        else:
            raise(Exception("Invalid color format. Expected (r, g, b, a) or (r, g, b). got: {}".format(color)))
    
    def _ensure_particle_capacity(self, required_count: int):
        """
        Ensure particle buffers are large enough - DYNAMIC RESIZING
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
        
        Args:
            x (int): X position from left (pygame coordinate system)
            y (int): Y position from top (pygame coordinate system)  
            width (int): Width of scissor region
            height (int): Height of scissor region
        """
        if not self._initialized:
            return
        x, y, width, height = int(x), int(y), int(width), int(height)
            
        glEnable(GL_SCISSOR_TEST)
        
        gl_scissor_y = self.height - (y + height)
        
        gl_scissor_x = max(0, x)
        gl_scissor_y = max(0, gl_scissor_y)
        gl_scissor_width = min(width, self.width - gl_scissor_x)
        gl_scissor_height = min(height, self.height - gl_scissor_y)
        
        glScissor(gl_scissor_x, gl_scissor_y, gl_scissor_width, gl_scissor_height)

    def disable_scissor(self):
        """Disable scissor test"""
        if not self._initialized:
            return
        glDisable(GL_SCISSOR_TEST)
    
    def draw_rect(self, x: int, y: int, width: int, height: int, 
              color: tuple, fill: bool = True, anchor_point: tuple = (0.0, 0.0), 
              border_width: int = 1, surface: Optional[pygame.Surface] = None,
              corner_radius: Tuple[int, int, int, int]|int = 0):
        """
        Draw a colored rectangle with optional rounded corners.
        
        Args:
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            width: Rectangle width
            height: Rectangle height
            color: RGB color tuple
            fill: Whether to fill the rectangle
            anchor_point: Anchor point for the rectangle
            border_width: Border width for unfilled rectangles
            surface: Target surface
            corner_radius: Radius of rounded corners in pixels.
                        Can be:
                        - int: Same radius for all corners (CSS: border-radius: 10px)
                        - tuple of 4 ints: (top-left, top-right, bottom-right, bottom-left) 
                        (CSS: border-radius: 10px 20px 30px 40px)
        """
        if not self._initialized:
            return
        
        # Apply anchor point
        x, y = x - int(anchor_point[0] * width), y - int(anchor_point[1] * height)
        
        if surface:
            old_surface = self._current_target
            self.set_surface(surface)
        
        # Check if we should use rounded rectangle
        if (isinstance(corner_radius, (tuple, list)) and 
            any(r > 0 for r in corner_radius)) or \
        (isinstance(corner_radius, (int, float)) and corner_radius > 0):
            
            # Convert to tuple of 4 values
            if isinstance(corner_radius, (int, float)):
                # Single value: apply to all corners
                radii = (corner_radius, corner_radius, corner_radius, corner_radius)
            elif len(corner_radius) == 2:
                # Two values: top-left/bottom-right, top-right/bottom-left
                radii = (corner_radius[0], corner_radius[1], corner_radius[0], corner_radius[1])
            elif len(corner_radius) == 3:
                # Three values: top-left, top-right/bottom-left, bottom-right
                radii = (corner_radius[0], corner_radius[1], corner_radius[2], corner_radius[1])
            elif len(corner_radius) >= 4:
                # Four or more values: top-left, top-right, bottom-right, bottom-left
                radii = (corner_radius[0], corner_radius[1], corner_radius[2], corner_radius[3])
            else:
                radii = (0, 0, 0, 0)
            
            # Check if all corners are 0 (sharp rectangle)
            if all(r == 0 for r in radii):
                self._draw_sharp_rect(x, y, width, height, color, fill, border_width)
            else:
                self._draw_rounded_rect(x, y, width, height, color, fill, border_width, radii)
        else:
            self._draw_sharp_rect(x, y, width, height, color, fill, border_width)
        
        if surface:
            self.set_surface(old_surface)

    def _draw_sharp_rect(self, x: int, y: int, width: int, height: int, 
                        color: tuple, fill: bool, border_width: int):
        """Original sharp-corner rectangle drawing (existing code)"""
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

    def _draw_rounded_rect(self, x: int, y: int, width: int, height: int, 
                       color: tuple, fill: bool, border_width: int, 
                       corner_radii: Tuple[int, int, int, int]):
        """Draw rectangle with individually rounded corners"""
        # Clamp corner radii to maximum possible value
        max_radius_x = width // 2
        max_radius_y = height // 2
        
        # Ensure radii don't exceed rectangle dimensions
        radii = (
            min(corner_radii[0], max_radius_x, max_radius_y),  # top-left
            min(corner_radii[1], max_radius_x, max_radius_y),  # top-right
            min(corner_radii[2], max_radius_x, max_radius_y),  # bottom-right
            min(corner_radii[3], max_radius_x, max_radius_y)   # bottom-left
        )
        
        # Convert color
        r_gl, g_gl, b_gl, a_gl = self._convert_color(color)
        
        # Use rounded rectangle shader
        glUseProgram(self.rounded_rect_shader.program)
        
        # Set uniforms
        glUniform2f(self.rounded_rect_shader._get_uniform_location("uScreenSize"), 
                    float(self.width), float(self.height))
        glUniform4f(self.rounded_rect_shader._get_uniform_location("uTransform"), 
                    float(x), float(y), float(width), float(height))
        glUniform4f(self.rounded_rect_shader._get_uniform_location("uColor"), 
                    r_gl, g_gl, b_gl, a_gl)
        glUniform4f(self.rounded_rect_shader._get_uniform_location("uCornerRadii"), 
                    float(radii[0]), float(radii[1]), 
                    float(radii[2]), float(radii[3]))
        glUniform2f(self.rounded_rect_shader._get_uniform_location("uRectSize"), 
                    float(width), float(height))
        glUniform1f(self.rounded_rect_shader._get_uniform_location("uFeather"), 
                    1.5)  # Edge smoothness in pixels
        glUniform1i(self.rounded_rect_shader._get_uniform_location("uFill"), 
                    1 if fill else 0)
        glUniform1f(self.rounded_rect_shader._get_uniform_location("uBorderWidth"), 
                    float(border_width))
        
        # Draw the rectangle
        glBindVertexArray(self.rounded_rect_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glUseProgram(0)
    
    def draw_line(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                  color: tuple, width: int = 2, surface: Optional[pygame.Surface] = None):
        """
        Draw a line between two points with specified width.
        
        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate
            color: RGB color tuple
            width: Line width
            surface: Target surface
        """
        if not self._initialized or not self.simple_shader.program:
            return
        
        if surface:
            old_surface = self._current_target
            self.set_surface(surface)
                
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
        
        if surface:
            self.set_surface(old_surface)
            
    def draw_lines(self, points:List[Tuple[Tuple[int, int], Tuple[int, int]]], color: Tuple[int, int, int, float]|Tuple[int,int,int], width: int = 2, surface: Optional[pygame.Surface] = None):
        for point in points:
            start_point, end_point = point
            self.draw_line(start_point[0], start_point[1], end_point[0], end_point[1], color, width, surface)

    def draw_text(self, text: str, x: int, y: int, color: tuple, font:pygame.font.FontType, surface: Optional[pygame.Surface] = None, anchor_point: tuple = (0.0, 0.0)):
        """
        Draw text using pygame font rendering
        """
        x, y = x - int(anchor_point[0] * font.size(text)[0]), y - int(anchor_point[1] * font.size(text)[1])
        if surface:
            text_surface = font.render(text, True, color)
            surface.blit(text_surface, (x, y))
        else:
            text_surface = font.render(text, True, color)
            self.blit(text_surface, (x, y))
    
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
    
    def draw_circle(self, center_x: int, center_y: int, radius: int, 
                color: tuple, fill: bool = True, border_width: int = 1, 
                surface: Optional[pygame.Surface] = None,
                anchor_point: Tuple[float, float] = (0.5, 0.5)):
        """
        Draw a circle with specified center, radius, color, and anchor point.
        
        Args:
            center_x: X coordinate where the anchor point will be placed
            center_y: Y coordinate where the anchor point will be placed
            radius: Circle radius
            color: RGB color tuple
            fill: Whether to fill the circle
            border_width: Border width for hollow circles
            surface: Target surface
            anchor_point: Anchor point within the circle's bounding box (0.0-1.0)
                        (0, 0) = top-left, (0.5, 0.5) = center, (1, 1) = bottom-right
        """
        if not self._initialized or not self.simple_shader.program:
            return
            
        if surface:
            old_surface = self._current_target
            self.set_surface(surface)
        
        # Calculate the bounding box size
        width = radius * 2
        height = radius * 2
        
        anchor_offset_x = width * anchor_point[0]
        anchor_offset_y = height * anchor_point[1]
        
        # Calculate top-left corner of bounding box
        x = center_x - anchor_offset_x
        y = center_y - anchor_offset_y
        
        # Generate circle geometry with caching for performance
        cache_key = (radius, fill, border_width)
        if cache_key in self._circle_cache:
            vao, vbo, ebo, vertex_count = self._circle_cache[cache_key]
        else:
            # Generate circle vertices - use more segments for larger circles
            segments = max(24, min(128, radius // 2))  # Adaptive segment count
            
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
        
        # Pass the bounding box (x, y, width, height)
        glUniform4f(self.simple_shader._get_uniform_location("uTransform"), 
                float(x), float(y), float(width), float(height))
        glUniform4f(self.simple_shader._get_uniform_location("uColor"), 
                r_gl, g_gl, b_gl, a_gl)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBindVertexArray(vao)
        glDrawElements(GL_TRIANGLES, vertex_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        glDisable(GL_BLEND)
        glUseProgram(0)
        
        if surface:
            self.set_surface(old_surface)
    
    def _generate_filled_circle_geometry(self, segments: int):
        """Generate vertices and indices for a filled circle - FIXED VERSION"""
        # Start with the center point
        vertices = [0.5, 0.5]  # Center is at (0.5, 0.5) in normalized coordinates
        
        # Generate perimeter vertices
        for i in range(int(segments + 1)):
            angle = 2 * np.pi * i / int(segments)
            # Circle perimeter points around the center
            vertices.extend([
                np.cos(angle) * 0.5 + 0.5,  # x: 0.0 to 1.0
                np.sin(angle) * 0.5 + 0.5   # y: 0.0 to 1.0
            ])
        
        # Generate indices for triangle fan
        indices = []
        # First vertex (index 0) is the center
        # Perimeter vertices start at index 1
        for i in range(1, int(segments)):
            indices.extend([0, i, i + 1])
        
        # Close the circle
        indices.extend([0, int(segments), 1])
        
        vertices = np.array(vertices, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        
        return vertices, indices
    
    def _generate_hollow_circle_geometry(self, segments: int, border_width: int, radius: int):
        """Generate vertices and indices for a hollow circle (outline)"""
        inner_radius = max(0.1, (radius - border_width) / (radius+1) * 0.5)
        outer_radius = 0.5
        
        vertices = []
        # Generate vertices for inner and outer circles
        for i in range(int(segments + 1)):
            angle = 2 * np.pi * i / segments
            # Outer vertex
            vertices.extend([np.cos(angle) * outer_radius + 0.5, np.sin(angle) * outer_radius + 0.5])
            # Inner vertex
            vertices.extend([np.cos(angle) * inner_radius + 0.5, np.sin(angle) * inner_radius + 0.5])
        
        indices = []
        for i in range(int(segments)):
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
    
    def draw_polygon(self, points: List[Tuple[int, int]], color: tuple, 
                     fill: bool = True, border_width: int = 1, surface: Optional[pygame.Surface] = None):
        """
        Draw a polygon from a list of points.
        
        Args:
            points: List of (x, y) points defining the polygon
            color: RGB color tuple
            fill: Whether to fill the polygon
            border_width: Border width for hollow polygons,
            surface: Target surface
        """
        if not self._initialized or not self.simple_shader.program or len(points) < 3:
            return
            
        if surface:
            old_surface = self._current_target
            self.set_surface(surface)
            
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
        
        if surface:
            self.set_surface(old_surface)
    
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
        """
        Draw a pygame surface at specified coordinates.
        Uses blit internally for consistency.
        
        Args:
            surface: Pygame surface to draw
            x: X coordinate
            y: Y coordinate
        """
        self.blit(surface, (x, y))
    
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
    
    def render_particles(self, particle_data: Dict[str, Any], camera: 'Camera'):
        """HIGHLY OPTIMIZED particle rendering with CORRECTED coordinate conversion"""
        if not self._initialized or not particle_data or particle_data['active_count'] == 0:
            return
        
        active_count = particle_data['active_count']
        
        # Ensure particle capacity
        self._ensure_particle_capacity(active_count)
        
        world_positions = particle_data['positions'][:active_count]
        
        screen_positions = np.zeros((active_count, 2), dtype=np.float32)
        for i, world_pos in enumerate(world_positions):
            screen_pos = camera.world_to_screen(world_pos)
            screen_positions[i] = [screen_pos.x, screen_pos.y]
        
        sizes = camera.convert_size_zoom_list(particle_data['sizes'][:active_count], 'ndarray')
        colors = particle_data['colors'][:active_count]
        alphas = particle_data['alphas'][:active_count]
        
        # Batch update instance data
        self._particle_instance_data[:active_count, 0] = screen_positions[:, 0]  # x
        self._particle_instance_data[:active_count, 1] = screen_positions[:, 1]  # y  
        self._particle_instance_data[:active_count, 2] = np.maximum(2.0, sizes)  # size
        self._particle_instance_data[:active_count, 3] = alphas / 255.0  # alpha
        
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
    
    def blit(self, source_surface: pygame.Surface, dest_rect: pygame.Rect, area: Optional[pygame.Rect] = None, 
         special_flags: int = 0):
        """
        Blit a source surface onto the current render target.
        Works similarly to pygame.Surface.blit().
        
        Args:
            source_surface: Surface to blit from
            dest_rect: Destination rectangle (x, y, width, height) or (x, y)
            area: Source area to blit from (None for entire surface)
            special_flags: Additional blitting flags (currently unused)
        """
        if not self._initialized or not self.texture_shader.program:
            return
            
        # Parse destination rectangle
        if isinstance(dest_rect, pygame.Rect):
            x, y, width, height = dest_rect
        else:
            x, y = dest_rect
            if type(source_surface) == pygame.Surface:
                width, height = source_surface.get_size()
        
        # Handle source area cropping
        if area is not None:
            # Create a subsurface from the specified area
            source_surface = source_surface.subsurface(area)
            # Reset destination size to match source area
            width, height = area.width, area.height
        
        # Convert surface to OpenGL texture
        texture_id = self._surface_to_texture(source_surface)
        
        # Set up rendering
        glUseProgram(self.texture_shader.program)
        
        glUniform2f(self.texture_shader._get_uniform_location("uScreenSize"), 
                float(self.width), float(self.height))
        glUniform4f(self.texture_shader._get_uniform_location("uTransform"), 
                float(x), float(y), float(width), float(height))
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glUniform1i(self.texture_shader._get_uniform_location("uTexture"), 0)
        
        # Set blending based on surface properties
        if source_surface.get_flags() & pygame.SRCALPHA:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_BLEND)
        
        # Draw the textured quad
        glBindVertexArray(self.texture_shader.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        
        # Clean up
        glDeleteTextures([texture_id])
        glUseProgram(0)

    def blit_surface(self, source_surface: pygame.Surface, dest_pos: Tuple[int, int], 
                    area: Optional[pygame.Rect] = None):
        """
        Alternative blit function with position tuple instead of rect.
        
        Args:
            source_surface: Surface to blit from
            dest_pos: Destination position (x, y)
            area: Source area to blit from
        """
        x, y = dest_pos
        width, height = source_surface.get_size()
        dest_rect = pygame.Rect(x, y, width, height)
        self.blit(source_surface, dest_rect, area)
        
    def fill_screen(self, color:Tuple[int, int, int, float]):
        c_r, c_g, c_b, c_a = self._convert_color(color)
        glClearColor(c_r, c_g, c_b, c_a)
        glClear(GL_COLOR_BUFFER_BIT)
    
    def cleanup(self):
        """Clean up OpenGL resources"""
        if not self._initialized:
            return
            
        # Clean up filters
        if self.filter_shader and self.filter_shader.program:
            glDeleteProgram(self.filter_shader.program)
        
        if self._filter_framebuffer:
            glDeleteFramebuffers(1, [self._filter_framebuffer])
        if self._filter_texture:
            glDeleteTextures(1, [self._filter_texture])
        if self._filter_renderbuffer:
            glDeleteRenderbuffers(1, [self._filter_renderbuffer])
    
        if self.simple_shader and self.simple_shader.program:
            glDeleteProgram(self.simple_shader.program)
        if self.texture_shader and self.texture_shader.program:
            glDeleteProgram(self.texture_shader.program)
        if self.particle_shader and self.particle_shader.program:
            glDeleteProgram(self.particle_shader.program)
        if self.rounded_rect_shader and self.rounded_rect_shader.program:
            glDeleteProgram(self.rounded_rect_shader.program)
        
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