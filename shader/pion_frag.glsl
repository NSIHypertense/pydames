#version 330 core

#include "lib.glsl"

uniform float t;
uniform float t_pre;
uniform vec2 fenetre_taille;
uniform vec2 fenetre_position;
uniform vec2 damier_taille;
uniform vec2 pion_position;
uniform vec2 pion_position_pre;
uniform int pion_couleur;
uniform bool pion_selection;
uniform bool pion_dame;

out vec4 frag_couleur;

void main() {
    vec2 uv = (gl_FragCoord.xy - fenetre_position) / fenetre_taille;
    vec2 _pion_position = pion_position_transition(t, t_pre, pion_position, pion_position_pre);
    uv = vec2(uv.x, 1.0 - uv.y) * damier_taille - 0.5 - _pion_position;

    float d = sqrt(dot(uv, uv));
    float c = 1.0 - clamp(d, 0.0, 1.0);

    if (pion_couleur == 1) {
        c /= 5.0;
    }

    for (float i = 1.0; i < 4.0; i++) {
        float r = i / 5.5;
        float r2 = smoothstep(r + 1.0 / 24.0, r, d);
        float r3 = smoothstep(r - 1.0 / 24.0, r - 1.0 / 16.0, d);

        c += (r3 - r2) / (24.0 / ((pion_couleur - 0.75) * 4.0));
    }

    float a = smoothstep(0.5 - 1.0 / 32.0, 0.5 - 2.0 / 32.0, d);

    frag_couleur = vec4(c, c, min(c + 0.02, 1.0), a);

    if (pion_selection) {
        a = smoothstep(1.0 / 2.3, 1.0 / 2.4, d);
        a *= smoothstep(1.0 / 2.5, 1.0 / 2.4, d);
        vec4 bordure = vec4(1.0, 0.0, 1.0, 1.0);

        frag_couleur = mix(frag_couleur, bordure, a);
    }

    if (pion_dame) {
        for (float i = 0.0; i < 3.0; i++) {
            vec2 n = rand2(pion_position);
            vec2 p = vec2(sin(t + i + (n.x + uv.x) * M_PI) + bruit(uv - t / 3.0) * i, cos(t - n.y * M_PI) + bruit(uv + t) * i);

            float d = distance_ligne(uv, -p, p);
            vec3 c = pion_couleur == 1 ? vec3(0.003, -0.007, -0.007) : vec3(0.001, 0.002, 0.007);

            frag_couleur = clamp(frag_couleur + vec4(c / d, 0.0), 0.0, 1.0);
        }
    }
}
