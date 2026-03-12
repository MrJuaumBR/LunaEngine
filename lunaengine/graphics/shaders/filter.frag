#version 330 core
out vec4 FragColor;
in vec2 TexCoord;

uniform sampler2D screenTexture;
uniform vec2 screenSize;
uniform float time;

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

float getRegionMask(vec2 pixelCoord) {
    if (regionType == 0) return 1.0; // Fullscreen
    
    if (regionType == 1) { // Rectangle
        vec2 rectMin = regionParams.xy;
        vec2 rectMax = regionParams.xy + regionParams.zw;
        
        vec2 dist = vec2(
            max(rectMin.x - pixelCoord.x, pixelCoord.x - rectMax.x),
            max(rectMin.y - pixelCoord.y, pixelCoord.y - rectMax.y)
        );
        
        float edgeDist = max(dist.x, dist.y);
        return 1.0 - smoothstep(0.0, feather, edgeDist);
    }
    else { // Circle
        vec2 center = regionParams.xy + regionParams.zw * 0.5;
        float dist = distance(pixelCoord, center);
        float effectiveRadius = min(regionParams.z, regionParams.w) * 0.5 * radius;
        return 1.0 - smoothstep(effectiveRadius - feather, effectiveRadius + feather, dist);
    }
}

// Filter implementations (simplified for space – same as in your 0.2.3 version)
vec3 applyVignette(vec3 color, vec2 uv) {
    vec2 center = uv - 0.5;
    float dist = length(center);
    float vignette = 1.0 - dist * 2.0 * intensity;
    vignette = smoothstep(0.0, 0.8, vignette);
    return color * vignette;
}

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

vec3 applySepia(vec3 color) {
    vec3 sepia = vec3(
        dot(color, vec3(0.393, 0.769, 0.189)),
        dot(color, vec3(0.349, 0.686, 0.168)),
        dot(color, vec3(0.272, 0.534, 0.131))
    );
    return mix(color, sepia, intensity);
}

vec3 applyGrayscale(vec3 color) {
    float gray = luminance(color);
    return mix(color, vec3(gray), intensity);
}

vec3 applyInvert(vec3 color) {
    vec3 inverted = vec3(1.0) - color;
    return mix(color, inverted, intensity);
}

vec3 applyWarmTemperature(vec3 color) {
    vec3 warm = vec3(1.0, 0.9, 0.7);
    return mix(color, color * warm, intensity);
}

vec3 applyColdTemperature(vec3 color) {
    vec3 cold = vec3(0.7, 0.9, 1.0);
    return mix(color, color * cold, intensity);
}

vec3 applyNightVision(vec3 color) {
    float green = luminance(color) * 1.5;
    float scanLine = sin(TexCoord.y * screenSize.y * 0.7 + time * 5.0) * 0.1 + 0.9;
    float noise = fract(sin(dot(TexCoord, vec2(12.9898, 78.233))) * 43758.5453) * 0.1;
    vec3 nightColor = vec3(0.0, green * scanLine + noise, 0.0);
    return mix(color, nightColor, intensity);
}

vec3 applyCRT(vec3 color) {
    float scanline = sin(TexCoord.y * screenSize.y * 0.7) * 0.04 + 0.96;
    vec2 uv = TexCoord - 0.5;
    float vignette = 1.0 - length(uv) * 0.7;
    float offset = 0.003;
    vec3 bleed;
    bleed.r = texture(screenTexture, TexCoord + vec2(offset, 0.0)).r;
    bleed.g = texture(screenTexture, TexCoord).g;
    bleed.b = texture(screenTexture, TexCoord - vec2(offset, 0.0)).b;
    vec3 crtColor = bleed * scanline * vignette;
    return mix(color, crtColor, intensity);
}

vec3 applyPixelate(vec3 color) {
    float pixelSize = 8.0 + (1.0 - intensity) * 15.0;
    vec2 pixelCoord = floor(TexCoord * screenSize / pixelSize) * pixelSize / screenSize;
    vec3 pixelated = texture(screenTexture, pixelCoord).rgb;
    return mix(color, pixelated, intensity);
}

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
    
    float brightness = luminance(color);
    float glow = smoothstep(0.7, 1.0, brightness);
    return mix(color, mix(color, blur, glow * 0.5), intensity);
}

vec3 applyEdgeDetect(vec3 color) {
    vec2 texelSize = 1.0 / screenSize;
    float gx[9] = float[9](-1.0, 0.0, 1.0, -2.0, 0.0, 2.0, -1.0, 0.0, 1.0);
    float gy[9] = float[9](-1.0, -2.0, -1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 1.0);
    
    float sx = 0.0, sy = 0.0;
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

vec3 applyEmboss(vec3 color) {
    vec2 texelSize = 1.0 / screenSize;
    float sample1 = luminance(texture(screenTexture, TexCoord + vec2(-texelSize.x, -texelSize.y)).rgb);
    float sample2 = luminance(texture(screenTexture, TexCoord + vec2(texelSize.x, texelSize.y)).rgb);
    float emboss = sample2 - sample1 + 0.5;
    return mix(color, vec3(emboss), intensity);
}

vec3 applySharpen(vec3 color) {
    vec2 texelSize = 1.0 / screenSize;
    vec3 blur = (texture(screenTexture, TexCoord + vec2(-texelSize.x, 0.0)).rgb +
                texture(screenTexture, TexCoord + vec2(texelSize.x, 0.0)).rgb +
                texture(screenTexture, TexCoord + vec2(0.0, -texelSize.y)).rgb +
                texture(screenTexture, TexCoord + vec2(0.0, texelSize.y)).rgb) * 0.25;
    vec3 sharp = color + (color - blur) * 2.0 * intensity;
    return mix(color, clamp(sharp, 0.0, 1.0), intensity);
}

vec3 applyPosterize(vec3 color) {
    float levels = 4.0 + (1.0 - intensity) * 12.0;
    vec3 posterized = floor(color * levels) / levels;
    return mix(color, posterized, intensity);
}

vec3 applyNeon(vec3 color) {
    vec2 texelSize = 1.0 / screenSize;
    float gx[9] = float[9](-1.0, 0.0, 1.0, -2.0, 0.0, 2.0, -1.0, 0.0, 1.0);
    float gy[9] = float[9](-1.0, -2.0, -1.0, 0.0, 0.0, 0.0, 1.0, 2.0, 1.0);
    
    vec3 sx = vec3(0.0), sy = vec3(0.0);
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
    vec3 hsv = rgb2hsv(color);
    hsv.y = 1.0; hsv.z = 1.0;
    vec3 neonColor = hsv2rgb(hsv) * edge * 3.0 * intensity;
    return mix(color, color + neonColor, intensity);
}

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

vec3 applyFisheye(vec3 color) {
    vec2 center = vec2(0.5, 0.5);
    vec2 uv = TexCoord - center;
    float dist = length(uv);
    float strength = 0.5 * intensity;
    vec2 distorted = uv * (1.0 - strength * dist * dist);
    vec2 sampleUV = center + distorted;
    if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0)
        return color;
    return texture(screenTexture, sampleUV).rgb;
}

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
    if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0)
        return color;
    return texture(screenTexture, sampleUV).rgb;
}

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
    vec2 pixelCoord = gl_FragCoord.xy;
    float regionMask = getRegionMask(pixelCoord);
    
    if (regionMask > 0.0 && filterType != 0) {
        vec3 filtered = applyFilter(color, filterType);
        color = mix(color, filtered, intensity * regionMask);
    }
    
    FragColor = vec4(color, original.a);
}