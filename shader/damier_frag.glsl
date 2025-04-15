#version 330 core

uniform float t;
uniform vec2 damier_taille;
uniform vec2 fenetre_taille;

in vec4 couleur;
out vec4 frag_couleur;

void main() {
	vec2 d = gl_FragCoord.xy / fenetre_taille * damier_taille * 2;
    if (couleur.w == 0 && couleur.xyz != vec3(0, 0, 0)) {
        frag_couleur = vec4(couleur.xyz, abs(sin(t * 4) * sin(t * 4 + d.x + d.y)) / 1.5);
    } else {
        frag_couleur = couleur;
    }
}

