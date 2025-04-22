#version 330 core

#include "lib.glsl"

uniform float t;
uniform vec2 fenetre_taille;
uniform vec2 fenetre_position;
uniform vec2 damier_taille;
uniform vec2 damier_curseur;

in vec4 couleur;
out vec4 frag_couleur;

void main() {
    vec2 uv = (gl_FragCoord.xy - fenetre_position) / fenetre_taille;

    if (couleur.w == 0 && couleur.xyz != vec3(0, 0, 0)) {
        vec2 d = uv * damier_taille * 2;
        float y = couleur.y * abs(cos(t / couleur.y + (d.x + d.y) * couleur.y)) / 2.0;
        float z = couleur.z * abs(sin(t * 4) * sin(t * 4 + d.x + d.y));
        frag_couleur = vec4(couleur.x, y / (couleur.z + 1.0), z, 1.0);
    } else {
        vec2 d = uv * damier_taille;
        float a = vignette(uv, 20.0, 0.75);
        vec2 uv_carre = mod(d, 1.0);
        float b = vignette(uv_carre, 50.0, 0.5);
        vec3 v = couleur.xyz * a * b;

        d.y = damier_taille.y - d.y;
        if (damier_curseur == floor(d)) {
            v = mix(v, vec3(sin((t + d.x + d.y) * 4.0) / 4.0 + 0.25), 0.4);
        }
        frag_couleur = vec4(v, couleur.w);
    }
}
