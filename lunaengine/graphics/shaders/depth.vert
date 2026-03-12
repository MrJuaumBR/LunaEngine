#version 330 core
layout (location = 0) in vec2 aPos;

uniform mat4 model;
uniform mat4 lightSpaceMatrix;      // used by directional

void main() {
    gl_Position = lightSpaceMatrix * model * vec4(aPos, 0.0, 1.0);
}