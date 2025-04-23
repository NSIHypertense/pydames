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
        vec4 x = couleur * abs(cos(t * 2.0 / couleur + (d.x + d.y) * couleur)) / 2.0;
        frag_couleur = vec4(x.xyz, 1.0);
    } else {
        vec2 d = uv * damier_taille;
        float a = vignette(uv, 20.0, 0.75);
        vec2 uv_carre = mod(d, 1.0);
        float b = vignette(uv_carre, 50.0, 0.5);
        vec3 v = couleur.xyz * a * b;

        d.y = damier_taille.y - d.y;
        if (damier_curseur == floor(d)) {
            d = (d - damier_curseur) * rotate2d(t * 2.0);
            v = clamp(v + vec3(sin((t + d.x + d.y) * 4.0) / 16.0 - (luminance(v) / 3.0 - 0.1)), 0.0, 1.0);
        }
        frag_couleur = vec4(v, couleur.w);
    }
}
