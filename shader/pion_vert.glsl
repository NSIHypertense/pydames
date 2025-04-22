#version 330 core

#include "lib.glsl"

uniform float t;
uniform float t_pre;
uniform vec2 damier_taille;
uniform vec2 pion_position;
uniform vec2 pion_position_pre;

layout(location = 0) in vec2 vert_position;

void main() {
    vec2 offset = vec2(1.0, -1.0) / damier_taille + vec2(-1.0, 1.0);
    vec2 _pion_position = pion_position_transition(t, t_pre, pion_position, pion_position_pre);
    gl_Position = vec4(
            vert_position / damier_taille + offset +
                _pion_position * vec2(2.0, -2.0) / damier_taille,
            0.0, 1.0);
}
