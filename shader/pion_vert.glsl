#version 330 core

uniform vec2 damier_taille;
uniform vec2 pion_position;

layout (location = 0) in vec2 vert_position;

void main() {
	vec2 offset = vec2(1.0, -1.0) / damier_taille + vec2(-1.0, 1.0);
    gl_Position = vec4(
		vert_position / damier_taille + offset +
		pion_position * vec2(2.0, -2.0) / damier_taille,
		0.0, 1.0);
}

