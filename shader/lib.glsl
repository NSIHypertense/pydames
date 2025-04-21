#define M_PI 3.1415926535897932384626433832795

// ombre autour de l'écran
float vignette(vec2 v, float i, float m) {
    v *= 1.0 - v.yx;
    return pow(v.x * v.y * i, 0.25) * m + (1.0 - m);
}

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
