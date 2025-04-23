#version 330 core

#include "lib.glsl"

uniform float t;
uniform vec2 fenetre_taille;

out vec4 frag_couleur;

void main() {
    vec2 taille = vec2(max(fenetre_taille.x, fenetre_taille.y));

    float sin_t_2 = sin(t) / 2.0;
    vec2 uv = (gl_FragCoord.xy / taille - vec2(0.5)) * (sin_t_2 / 2.0 + 1.0) * 8;

    vec2 uv_ = uv * 0.75;
    float t_4 = t / 4.0;
    vec2 n = vec2(bruit(uv_ * sin(t_4)), bruit(uv_ * cos(t_4)));

    vec2 n_5 = n / 5.0;
    float cos_t2 = cos(t) * 2.0;
    float a = float((int(uv.x + 20.0 + t + n_5.x) + int(uv.y + 20.0 + cos_t2 + n_5.y)) % 2) * (sin_t_2 / 25.0 + 0.02);

    vec4 d = mix(vec4(n.x, 0.0, n.x + n.y, 0.0), vec4(0.0), a);

    float bleu = a + abs(cos(t * 0.75) / 2.0);

    frag_couleur = vec4(vec3(a, a, bleu), 1.0);
    frag_couleur = clamp(frag_couleur + d, 0.0, 1.0);
}
