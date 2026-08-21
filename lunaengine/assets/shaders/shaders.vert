#version 330 core

// ============================================================
// PARTICLE VERTEX SHADER
// ============================================================
#ifdef LUNA_SHADER_PARTICLE
layout (location = 0) in vec2 aPos;               // not used (dummy)
layout (location = 1) in vec4 instanceData;       // x, y, size, alpha
layout (location = 2) in vec4 instanceColor;      // r, g, b, a

uniform vec2 uScreenSize;

out vec4 vColor;
out float vAlpha;

void main() {
    // instanceData.xy = screen position
    // instanceData.z  = size
    // instanceData.w  = alpha
    vec2 screenPos = instanceData.xy;
    
    // Convert to normalized device coordinates
    vec2 ndc = vec2(
        (screenPos.x / uScreenSize.x) * 2.0 - 1.0,
        1.0 - (screenPos.y / uScreenSize.y) * 2.0
    );
    
    gl_Position = vec4(ndc, 0.0, 1.0);
    gl_PointSize = instanceData.z;
    vColor = instanceColor;
    vAlpha = instanceData.w;
}
#endif

// ============================================================
// SIMPLE VERTEX SHADER (solid color)
// ============================================================
#ifdef LUNA_SHADER_SIMPLE
layout (location = 0) in vec2 aPos;

uniform vec2 uScreenSize;
uniform vec4 uTransform; // x, y, width, height

void main() {
    // Convert to pixel coordinates
    vec2 pixelPos = aPos * uTransform.zw + uTransform.xy;
    
    // Convert to normalized device coordinates
    vec2 ndc = vec2(
        (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
        1.0 - (pixelPos.y / uScreenSize.y) * 2.0
    );
    
    gl_Position = vec4(ndc, 0.0, 1.0);
}
#endif

// ============================================================
// TEXTURE VERTEX SHADER
// ============================================================
#ifdef LUNA_SHADER_TEXTURE
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;
uniform vec2 uScreenSize;
uniform vec4 uTransform; // x, y, width, height

void main() {
    vec2 pixelPos = aPos * uTransform.zw + uTransform.xy;
    vec2 ndc = vec2(
        (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
        1.0 - (pixelPos.y / uScreenSize.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    TexCoord = aTexCoord;
}
#endif

// ============================================================
// ROUNDED RECT VERTEX SHADER
// ============================================================
#ifdef LUNA_SHADER_ROUNDED_RECT
layout (location = 0) in vec2 aPos;

out vec2 vPos;
uniform vec2 uScreenSize;
uniform vec4 uTransform; // x, y, width, height
uniform float uFeather; // Edge smoothness

void main() {
    vec2 pixelPos = aPos * uTransform.zw + uTransform.xy;
    vec2 ndc = vec2(
        (pixelPos.x / uScreenSize.x) * 2.0 - 1.0,
        1.0 - (pixelPos.y / uScreenSize.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    vPos = aPos;
}
#endif

// ============================================================
// FILTER VERTEX SHADER (fullscreen quad)
// ============================================================
#ifdef LUNA_SHADER_FILTER
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
    TexCoord = aTexCoord;
}
#endif

// ============================================================
// DEPTH VERTEX SHADER (shadow mapping)
// ============================================================
#ifdef LUNA_SHADER_DEPTH
layout (location = 0) in vec2 aPos;

uniform mat4 model;
uniform mat4 lightSpaceMatrix;      // used by directional

void main() {
    gl_Position = lightSpaceMatrix * model * vec4(aPos, 0.0, 1.0);
}
#endif

// ============================================================
// MASK VERTEX SHADER (fullscreen quad for compositing)
// ============================================================
#ifdef LUNA_SHADER_MASK
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
    TexCoord = aTexCoord;
}
#endif