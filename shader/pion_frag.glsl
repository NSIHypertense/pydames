#version 330 core

#define M_PI 3.1415926535897932384626433832795

uniform float t;
uniform vec2 fenetre_taille;
uniform vec2 damier_taille;
uniform vec2 pion_position;
uniform int pion_couleur;
uniform bool pion_selection;

out vec4 frag_couleur;

void main() {
	vec2 uv = gl_FragCoord.xy / fenetre_taille;
	uv = vec2(uv.x, 1.0 - uv.y) * damier_taille - 0.5 - pion_position;

	float d = sqrt(dot(uv, uv));
	float c = 1.0 - clamp(d, 0.0, 1.0);
	if (pion_couleur == 1) {
		c /= 6.0;
	}
	
	for (float i = 1.0; i < 4.0; i++) {
		float r = i / 5.5;
		float r2 = smoothstep(r + 1.0 / 24.0, r, d);
		float r3 = smoothstep(r - 1.0 / 24.0, r - 1.0 / 16.0, d);

		if (pion_couleur == 1) {
			c -= (r3 - r2) / 8.0;
		} else {
			c += (r3 - r2) / 6.0;
		}
	}

	float a = smoothstep(0.5 - 1.0 / 32.0, 0.5 - 2.0 / 32.0, d);

	frag_couleur = vec4(c, c, c, a);

	if (pion_selection) {
		a = smoothstep(1.0 / 2.3, 1.0 / 2.4, d);
        a *= smoothstep(1.0 / 2.5, 1.0 / 2.4, d);
		vec4 bordure = vec4(1.0, 0.0, 1.0, 1.0);
    
        frag_couleur = mix(frag_couleur, bordure, a);
	}
}

