#version 330 core
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