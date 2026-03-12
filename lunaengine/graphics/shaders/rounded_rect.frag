#version 330 core
out vec4 FragColor;
in vec2 vPos;

uniform vec4 uColor;
uniform vec4 uCornerRadii; // top-left, top-right, bottom-right, bottom-left
uniform float uFeather;
uniform vec2 uRectSize;
uniform int uFill; // 1 = filled, 0 = outline
uniform float uBorderWidth;

// Signed distance function for a rounded rectangle with per-corner radii
float roundedRectSDF(vec2 p, vec2 b, vec4 r) {
    r.xy = (p.x > 0.0) ? r.yw : r.xz;
    r.x  = (p.y > 0.0) ? r.x : r.y;
    
    vec2 q = abs(p) - b + r.x;
    return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - r.x;
}

void main() {
    vec2 pixelPos = vPos * uRectSize;
    vec2 center = uRectSize * 0.5;
    vec2 centeredPos = pixelPos - center;
    vec2 halfSize = center;
    
    float distance = roundedRectSDF(centeredPos, halfSize, uCornerRadii);
    
    if (uFill == 1) {
        // Filled rectangle
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