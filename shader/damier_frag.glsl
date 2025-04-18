#version 330 core

uniform float t;
uniform vec2 damier_taille;
uniform vec2 fenetre_taille;
uniform vec2 fenetre_position;

in vec4 couleur;
out vec4 frag_couleur;

float vignette(vec2 v, float i, float m) {
    v *= 1.0 - v.yx;
    return pow(v.x * v.y * i, 0.25) * m + (1.0 - m);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - fenetre_position) / fenetre_taille;
    vec2 d = uv * damier_taille * 2;

    if (couleur.w == 0 && couleur.xyz != vec3(0, 0, 0)) {
        frag_couleur = vec4(couleur.xyz, abs(sin(t * 4) * sin(t * 4 + d.x + d.y)) / 1.5);
    } else {
        float a = vignette(uv, 20.0, 0.75);
        vec2 uv_carre = mod(uv * damier_taille, 1.0);
        float b = vignette(uv_carre, 50.0, 0.5);
        frag_couleur = vec4(couleur.xyz * a * b, couleur.w);
    }
}
