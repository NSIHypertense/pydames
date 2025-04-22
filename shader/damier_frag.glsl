#version 330 core

#include "lib.glsl"

uniform float t;
uniform vec2 damier_taille;
uniform vec2 fenetre_taille;
uniform vec2 fenetre_position;

in vec4 couleur;
out vec4 frag_couleur;

void main() {
    vec2 uv = (gl_FragCoord.xy - fenetre_position) / fenetre_taille;
    vec2 d = uv * damier_taille * 2;

    if (couleur.w == 0 && couleur.xyz != vec3(0, 0, 0)) {
        float a = couleur.z * abs(sin(t * 4) * sin(t * 4 + d.x + d.y));
        float b = couleur.y * abs(cos(t / couleur.y + (d.x + d.y) * couleur.y)) / 2.0;
        frag_couleur = vec4(couleur.x, b / (couleur.z + 1.0), a, 1.0);
    } else {
        float a = vignette(uv, 20.0, 0.75);
        vec2 uv_carre = mod(uv * damier_taille, 1.0);
        float b = vignette(uv_carre, 50.0, 0.5);
        frag_couleur = vec4(couleur.xyz * a * b, couleur.w);
    }
}
