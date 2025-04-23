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

uniform float duree_animation;
uniform vec3 couleur_noir;
uniform vec3 couleur_blanc;
uniform vec3 couleur_dame_noir;
uniform vec3 couleur_dame_blanc;
uniform vec3 couleur_bordure;

out vec4 frag_couleur;

void main() {
    vec2 uv = (gl_FragCoord.xy - fenetre_position) / fenetre_taille;
    vec2 _pion_position = pion_position_animation(t, t_pre, duree_animation, pion_position, pion_position_pre);
    uv = vec2(uv.x, 1.0 - uv.y) * damier_taille - 0.5 - _pion_position;

    float d = sqrt(dot(uv, uv));
    float c = 1.0 - clamp(d, 0.0, 1.0);

    for (float i = 1.0; i < 4.0; i++) {
        float r = i / 5.5;
        float r2 = smoothstep(r + 1.0 / 24.0, r, d);
        float r3 = smoothstep(r - 1.0 / 24.0, r - 1.0 / 16.0, d);

        c += (r3 - r2) / 5.0;
    }

    c /= 2.0;

    vec3 couleur = pion_couleur == 1 ? couleur_noir : couleur_blanc;
    vec3 couleur_dame = pion_couleur == 1 ? couleur_dame_noir : couleur_dame_blanc;
    float a = smoothstep(0.5 - 1.0 / 32.0, 0.5 - 2.0 / 32.0, d);

    frag_couleur = vec4(clamp(vec3(c) * max(vec3(0.2), couleur * 1.3) + couleur * 0.4, 0.0, 1.0), a);

    if (pion_selection) {
        a = smoothstep(1.0 / 2.3, 1.0 / 2.4, d);
        a *= smoothstep(1.0 / 2.5, 1.0 / 2.4, d);

        frag_couleur = mix(frag_couleur, vec4(couleur_bordure, 1.0), a);
    }

    if (pion_dame) {
        vec3 ombre = vec3(0.0);
        vec2 _uv = uv * rotate2d(t * 2.0);
        float x = sin((t + _uv.x + _uv.y) * 6.0);
        vec3 effet = couleur_dame * x / 8.0;
        if (x < 0.0) {
            effet = effet.zyx;
        }

        frag_couleur = min(frag_couleur + vec4(effet, 0.0), 1.0);

        for (int j = 0; j < 2; j++) {
            for (float i = 0.0; i < 3.0; i++) {
                vec2 n = rand2(pion_position);
                vec2 p = vec2(sin(t + i + (n.x + uv.x) * M_PI) + bruit(uv - t / 3.0) * i, cos(t - n.y * M_PI) + bruit(uv + t) * i);

                float d = distance_ligne(uv, -p, p);

                if (j == 0) {
                    ombre = min(ombre + min(vec3(0.003 / d), 0.1), luminance(couleur));
                } else {
                    vec4 eclair = vec4(couleur_dame / 150.0 / d, 0.0);
                    frag_couleur = clamp(frag_couleur - vec4(ombre, 0.0) + eclair, 0.0, 1.0);
                }
            }
        }
    }
}
