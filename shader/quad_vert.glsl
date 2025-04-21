#version 330 core

out vec2 vert_position;

void main() {
    vert_position = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
    gl_Position = vec4(vert_position * 2.0 - 1.0, 0.0, 1.0);
}
