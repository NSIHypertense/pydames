#version 330 core

layout (location = 0) in vec3 vert_position;
layout (location = 1) in vec4 vert_couleur;
out vec4 couleur;

void main() {
    gl_Position = vec4(vert_position, 1.0);
    couleur = vert_couleur;
}

