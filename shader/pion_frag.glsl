#version 330 core

#define M_PI 3.1415926535897932384626433832795

uniform float t;
uniform vec2 fenetre_taille;
uniform vec2 damier_taille;
uniform vec2 pion_position;
uniform int pion_couleur;
uniform bool pion_selection;
uniform bool pion_dame;

out vec4 frag_couleur;

// trouve la distance entre le point donné et le point sur le segment le plus proche
float distance_ligne(vec2 p, vec2 a, vec2 b) {
    vec2 ab = b - a;
    vec2 ap = p - a;

    // projection du vecteur ap vers ab
    float h = clamp(dot(ap, ab) / dot(ab, ab), 0.0, 1.0);
    // point plus proche du segment ab
    vec2 p1 = mix(a, b, h);

    // distance
    return length(p1 - p);
}

// nombres pseudo-aléatoires
// source : https://thebookofshaders.com/10/
float rand(vec2 v) {
    return fract(sin(dot(v.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}
vec2 rand2(vec2 v) {
    v = vec2(dot(v, vec2(127.1, 311.7)), dot(v, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(v) * 43758.5453123);
}

// source : https://thebookofshaders.com/11/
float bruit(vec2 v) {
    vec2 i = floor(v); // partie entière
    vec2 f = fract(v); // partie décimale

    // 4 coins
    float a = rand(i);
    float b = rand(i + vec2(1.0, 0.0));
    float c = rand(i + vec2(0.0, 1.0));
    float d = rand(i + vec2(1.0, 1.0));

    // courbe d'interpolation quintique
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);

    // interpolation du dégradé
    return mix(mix(dot(rand2(i + vec2(0.0, 0.0)), f - vec2(0.0, 0.0)),
            dot(rand2(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0)), u.x),
        mix(dot(rand2(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0)),
            dot(rand2(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0)), u.x), u.y);
}

void main() {
    vec2 uv = gl_FragCoord.xy / fenetre_taille;
    uv = vec2(uv.x, 1.0 - uv.y) * damier_taille - 0.5 - pion_position;

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
            vec3 c = pion_couleur == 1 ? vec3(0.01, 0.01, 0.03) : vec3(-0.007, -0.02, -0.02);

            frag_couleur = clamp(frag_couleur + vec4(c / d, 0.0), 0.0, 1.0);
        }
    }
}
