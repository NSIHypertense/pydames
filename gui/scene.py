from abc import ABC, abstractmethod

import numpy as np
from OpenGL import GL

DAMIER_LONGUEUR = 8
DAMIER_LARGEUR  = 8

VERTEX_SHADER_SRC = """
#version 330 core

layout (location = 0) in vec3 vert_position;
layout (location = 1) in vec4 vert_couleur;
out vec4 couleur;

void main() {
    gl_Position = vec4(vert_position, 1.0);
    couleur = vert_couleur;
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core

uniform float t;

in vec4 couleur;
out vec4 frag_couleur;

void main() {
    if (couleur.w == 0 && couleur.xyz != vec3(0, 0, 0)) {
        frag_couleur = vec4(couleur.xyz, abs(sin(t * 4)) / 1.5);
    } else {
        frag_couleur = couleur;
    }
}
"""

def verifier_shader(shader):
    success = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
    if not success:
        info_log = GL.glGetShaderInfoLog(shader)
        print(f"erreur de compilation du shader: {info_log.decode()}")
        
def verifier_programme(program):
    success = GL.glGetProgramiv(program, GL.GL_LINK_STATUS)
    if not success:
        info_log = GL.glGetProgramInfoLog(program)
        print(f"erreur de liaison du programme: {info_log.decode()}")

class Scene(ABC):
    @abstractmethod
    def rendre(self, t):
        pass

class SceneDamier(Scene):
    class _GLDamier:
        def __init__(self, damier_overlay: bool=False):
            sommets = []
            couleurs = []
            step_x = 2.0 / DAMIER_LONGUEUR
            step_y = 2.0 / DAMIER_LARGEUR
            
            for y in range(DAMIER_LARGEUR):
                for x in range(DAMIER_LONGUEUR):
                    x0 = x * step_x - 1
                    y0 = y * step_y - 1
                    x1 = x0 + step_x
                    y1 = y0 + step_y

                    sommets.extend([x0, y0, 0, x1, y0, 0, x0, y1, 0])
                    sommets.extend([x1, y0, 0, x1, y1, 0, x0, y1, 0])

                    if damier_overlay:
                        c = [0, 0, 0, 0]
                    else:
                        c = [1, 1, 1, 1] if (x + y) % 2 == 0 else [0, 0, 0, 1]

                    couleurs.extend(c * 6)
            
            sommets = np.array(sommets, dtype=np.float32)
            couleurs = np.array(couleurs, dtype=np.float32)
            
            self.vao = GL.glGenVertexArrays(1)
            GL.glBindVertexArray(self.vao)
            
            self.buffer_sommets = GL.glGenBuffers(1)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_sommets)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, sommets.nbytes, sommets, GL.GL_STATIC_DRAW)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(0)
            
            self.buffer_couleurs = GL.glGenBuffers(1)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_couleurs)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, couleurs.nbytes, couleurs,
                            GL.GL_DYNAMIC_DRAW if damier_overlay else GL.GL_STATIC_DRAW)
            GL.glVertexAttribPointer(1, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(1)
            
            GL.glBindVertexArray(0)

        def set_cases(self, cases_possibles):
            couleurs = []
            c = (-1, 0) if cases_possibles == [] else cases_possibles.pop(0)

            for y in range(DAMIER_LARGEUR):
                for x in range(DAMIER_LONGUEUR):
                    if c[0] == x and c[1] == y:
                        couleur = [1, 0, 1, 0]
                        couleurs.extend(couleur * 6)
                        if cases_possibles != []:
                            c = cases_possibles.pop(0)
                    else:
                        couleur = [0, 0, 0, 0]
                        couleurs.extend(couleur * 6)

            couleurs = np.array(couleurs, dtype=np.float32)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_couleurs)
            GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, couleurs.nbytes, couleurs)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        def rendre(self):
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glBindVertexArray(self.vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, DAMIER_LONGUEUR * DAMIER_LARGEUR * 6)
            GL.glBindVertexArray(0)
            GL.glDisable(GL.GL_BLEND)

        def __del__(self):
            GL.glDeleteBuffers(2, [self.buffer_sommets, self.buffer_couleurs])
            GL.glDeleteVertexArrays(1, [self.vao])

    def __init__(self):
        self.__cases_possibles = []

        self.programme = self.__creer_programme_shader()
        self.uniform_t = GL.glGetUniformLocation(self.programme, "t")
        self.damier = SceneDamier._GLDamier()
        self.overlay = SceneDamier._GLDamier(True)

        self.overlay.set_cases([(1, 1), (3, 4)]) # test de cases

    def __creer_programme_shader(self):
        vertex_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertex_shader, VERTEX_SHADER_SRC)
        GL.glCompileShader(vertex_shader)
        verifier_shader(vertex_shader)
        
        fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragment_shader, FRAGMENT_SHADER_SRC)
        GL.glCompileShader(fragment_shader)
        verifier_shader(vertex_shader)
        
        programme = GL.glCreateProgram()
        GL.glAttachShader(programme, vertex_shader)
        GL.glAttachShader(programme, fragment_shader)
        GL.glLinkProgram(programme)
        verifier_programme(programme)
        
        GL.glDeleteShader(vertex_shader)
        GL.glDeleteShader(fragment_shader)

        return programme

    def rendre(self, t):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glUseProgram(self.programme)
        GL.glUniform1f(self.uniform_t, t)
        self.damier.rendre()
        self.overlay.rendre()
        GL.glUseProgram(0)

    @property
    def cases_possibles(self):
        return self.__cases_possibles

    @cases_possibles.setter
    def cases_possibles(self, cases):
        for c in cases:
            assert isinstance(c, tuple)
            assert 0 <= c[0] < DAMIER_LONGUEUR
            assert 0 <= c[1] < DAMIER_LARGEUR

        self.__cases_possibles = sorted(cases)

