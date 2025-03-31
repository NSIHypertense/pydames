#version 330 core

uniform float t;

in vec4 couleur;
out vec4 frag_couleur;

void main() {
    if (couleur.w == 0 && couleur.xyz != vec3(0, 0, 0)) {
        frag_couleur = vec4(couleur.xyz, abs(sin(t * 4)) / 1.5);
    } else {
        frag_couleur = couleur;
    }
}

