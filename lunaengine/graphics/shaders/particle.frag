#version 330 core
in vec4 vColor;
in float vAlpha;
out vec4 FragColor;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    if (length(coord) > 0.5) discard;
    FragColor = vec4(vColor.rgb, vColor.a * vAlpha);
}