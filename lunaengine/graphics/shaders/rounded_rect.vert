#version 330 core
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