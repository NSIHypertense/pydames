from abc import ABC, abstractmethod
import math
import threading
import traceback

import numpy as np
from OpenGL import GL
import imgui

import mp.client
import util

DAMIER_LONGUEUR = 8
DAMIER_LARGEUR = 8


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


def creer_programme_shader(vert: str, frag: str):
    vertex_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)

    with util.resource(vert) as f:
        GL.glShaderSource(vertex_shader, f.read())

    GL.glCompileShader(vertex_shader)
    verifier_shader(vertex_shader)

    fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)

    with util.resource(frag) as f:
        GL.glShaderSource(fragment_shader, f.read())

    GL.glCompileShader(fragment_shader)
    verifier_shader(fragment_shader)

    programme = GL.glCreateProgram()
    GL.glAttachShader(programme, vertex_shader)
    GL.glAttachShader(programme, fragment_shader)
    GL.glLinkProgram(programme)
    verifier_programme(programme)

    GL.glDeleteShader(vertex_shader)
    GL.glDeleteShader(fragment_shader)

    return programme


class Scene(ABC):
    @property
    @abstractmethod
    def longueur(self) -> int:
        pass

    @longueur.setter
    @abstractmethod
    def longueur(self, x: int):
        pass

    @property
    @abstractmethod
    def largeur(self) -> int:
        pass

    @largeur.setter
    @abstractmethod
    def largeur(self, x: int):
        pass

    @property
    @abstractmethod
    def prochaine_scene(self) -> "Scene | None":
        pass

    @prochaine_scene.setter
    @abstractmethod
    def prochaine_scene(self, x: "Scene"):
        pass

    @abstractmethod
    def rendre(self, t):
        pass


class SceneTitre(Scene):
    prochaine_scene = None
    longueur = None
    largeur = None

    def __init__(self):
        self.popup_commencer = False
        self.destination = "127.0.0.1"
        self.port = "2332"
        self.connexion = False
        self.connexion_erreur = 0
        self.thread_connexion = None

        self.quitter = False

    def __connecter(self, t):
        def creer_socket():
            try:
                mp.client.sock = mp.client.connecter(self.destination, int(self.port))
                mp.client.demarrer_client()
            except OSError:
                print(traceback.format_exc())
                self.connexion = False
                self.connexion_erreur = t + 2

        self.thread_connexion = threading.Thread(target=creer_socket)
        self.thread_connexion.start()

    def rendre(self, t):
        io = imgui.get_io()

        longueur_fenetre = io.display_size.x
        largeur_fenetre = io.display_size.y
        longueur, largeur = int(longueur_fenetre / 1.5), largeur_fenetre // 2

        imgui.set_next_window_size(longueur, largeur)
        imgui.set_next_window_position(
            (longueur_fenetre - longueur) // 2, (largeur_fenetre - largeur) // 2
        )

        imgui.begin(
            "Menu principal",
            False,
            imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE,
        )

        imgui.dummy(1, 50)

        titre = "pydames"
        imgui.set_cursor_pos_x((longueur - imgui.calc_text_size(titre)[0]) / 2)
        imgui.text(titre)

        imgui.dummy(1, 30)

        longueur_bouton = 150
        largeur_bouton = 30

        imgui.set_cursor_pos_x((longueur - longueur_bouton) / 2)
        if imgui.button("Commencer", longueur_bouton, largeur_bouton):
            self.popup_commencer = True

        imgui.set_cursor_pos_x((longueur - longueur_bouton) / 2)
        if imgui.button("Réglages", longueur_bouton, largeur_bouton):
            print("Les réglages ne sont pas implémentés.")

        imgui.set_cursor_pos_x((longueur - longueur_bouton) / 2)
        if imgui.button("Quitter", longueur_bouton, largeur_bouton):
            self.quitter = True

        imgui.end()

        if self.popup_commencer:
            imgui.open_popup("Commencer")

        longueur_popup = longueur_fenetre // 2
        largeur_popup = largeur_fenetre // 4

        imgui.set_next_window_size(longueur_popup, largeur_popup)
        imgui.set_next_window_position(
            (longueur_fenetre - longueur_popup) / 2,
            (largeur_fenetre - largeur_popup) / 2,
        )

        with imgui.begin_popup_modal(
            "Commencer", flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE
        ) as popup:
            if popup.opened:
                imgui.text("Connectez-vous à un serveur :")

                if self.connexion:
                    imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
                    imgui.push_style_var(
                        imgui.STYLE_ALPHA, imgui.get_style().alpha * 0.5
                    )

                _, self.destination = imgui.input_text(
                    "Destination", self.destination, -1
                )
                _, self.port = imgui.input_text(
                    "Port", self.port, -1, imgui.INPUT_TEXT_CHARS_DECIMAL
                )

                if imgui.button("Connecter"):
                    print(f"Connexion en cours: {(self.destination, self.port)}")
                    self.connexion = True
                    self.__connecter(t)
                elif self.connexion:
                    imgui.pop_style_var()
                    imgui.internal.pop_item_flag()

                    c = abs(math.sin(t * 6))
                    imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha * c)
                    imgui.text("Connexion en cours...")
                    imgui.pop_style_var()

                    if mp.client.connexion_erreur:
                        self.connexion = False
                        self.connexion_erreur = t + 2
                    elif mp.client.connexion_succes:
                        self.connexion = False
                        self.prochaine_scene = SceneDamier()
                        self.popup_commencer = False
                        imgui.close_current_popup()
                elif t < self.connexion_erreur:
                    imgui.push_style_var(
                        imgui.STYLE_ALPHA,
                        imgui.get_style().alpha * (self.connexion_erreur - t) / 2,
                    )
                    imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0)
                    imgui.text("Erreur de connexion!")
                    imgui.pop_style_color(1)
                    imgui.pop_style_var()


class SceneDamier(Scene):
    class _GLDamier:
        def __init__(self, damier_overlay: bool = False):
            self.damier_overlay = damier_overlay

            # test overlay
            sommets, couleurs = self.generer_buffers([(0, 1), (2, 1)])

            sommets = np.array(sommets, dtype=np.float32)
            couleurs = np.array(couleurs, dtype=np.float32)

            self.vao = GL.glGenVertexArrays(1)
            GL.glBindVertexArray(self.vao)

            self.buffer_sommets = GL.glGenBuffers(1)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_sommets)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER,
                sommets.nbytes,
                sommets,
                GL.GL_DYNAMIC_DRAW if damier_overlay else GL.GL_STATIC_DRAW,
            )
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(0)

            self.buffer_couleurs = GL.glGenBuffers(1)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_couleurs)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER,
                couleurs.nbytes,
                couleurs,
                GL.GL_DYNAMIC_DRAW if damier_overlay else GL.GL_STATIC_DRAW,
            )
            GL.glVertexAttribPointer(1, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(1)

            GL.glBindVertexArray(0)

        def generer_buffers(
            self, cases_possibles: list[tuple[int, int]]
        ) -> tuple[list[float], list[float]]:
            sommets = []
            couleurs = []
            mx = 2 / DAMIER_LONGUEUR
            my = 2 / DAMIER_LARGEUR

            case = (-1, 0) if cases_possibles == [] else cases_possibles.pop(0)

            for y in range(DAMIER_LARGEUR):
                for x in range(DAMIER_LONGUEUR):
                    if not self.damier_overlay or (case[0] == x and case[1] == y):
                        x0 = x * mx - 1
                        y0 = (DAMIER_LARGEUR - 1 - y) * my - 1
                        x1 = x0 + mx
                        y1 = y0 + my

                        sommets.extend([x0, y0, 0, x1, y0, 0, x0, y1, 0])
                        sommets.extend([x1, y0, 0, x1, y1, 0, x0, y1, 0])

                        if self.damier_overlay:
                            couleur = [1, 0, 1, 0]
                            if cases_possibles != []:
                                case = cases_possibles.pop(0)
                        else:
                            couleur = [1, 1, 1, 1] if (x + y) % 2 == 0 else [0, 0, 0, 1]

                        couleurs.extend(couleur * 6)

            return sommets, couleurs

        def set_cases(self, cases_possibles: list[tuple[int, int]]):
            sommets, couleurs = self.generer_buffers([])

            couleurs = np.array(couleurs, dtype=np.float32)
            sommets = np.array(sommets, dtype=np.float32)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_couleurs)
            GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, couleurs.nbytes, couleurs)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_sommets)
            GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, sommets.nbytes, sommets)

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

    class _GLPion:
        buffer_sommets = None

        @classmethod
        def creer_buffer_sommets(cls):
            sommets = np.array(
                [-1, 1, 1, 1, 1, -1, 1, -1, -1, -1, -1, 1],
                dtype=np.float32,
            )  # carré
            cls.buffer_sommets = GL.glGenBuffers(1)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, cls.buffer_sommets)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER, sommets.nbytes, sommets, GL.GL_STATIC_DRAW
            )
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        def __init__(self, position: tuple[int, int]):
            self.position = position

            self.programme = creer_programme_shader(
                "shader/pion_vert.glsl", "shader/pion_frag.glsl"
            )
            self.uniform_damier_taille = GL.glGetUniformLocation(
                self.programme, "damier_taille"
            )
            self.uniform_pion_position = GL.glGetUniformLocation(
                self.programme, "pion_position"
            )
            self.uniform_fenetre_taille = GL.glGetUniformLocation(
                self.programme, "fenetre_taille"
            )
            self.uniform_t = GL.glGetUniformLocation(self.programme, "t")

            GL.glUseProgram(self.programme)
            GL.glUniform2f(self.uniform_damier_taille, DAMIER_LONGUEUR, DAMIER_LARGEUR)
            GL.glUseProgram(0)

            if not SceneDamier._GLPion.buffer_sommets:
                SceneDamier._GLPion.creer_buffer_sommets()

            self.vao = GL.glGenVertexArrays(1)
            GL.glBindVertexArray(self.vao)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, SceneDamier._GLPion.buffer_sommets)
            GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(0)
            GL.glBindVertexArray(0)

        def rendre(self, t, longueur, largeur):
            GL.glUseProgram(self.programme)

            GL.glUniform1f(self.uniform_t, t)
            GL.glUniform2f(self.uniform_pion_position, *self.position)
            GL.glUniform2f(self.uniform_fenetre_taille, longueur, largeur)

            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

            GL.glBindVertexArray(self.vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
            GL.glBindVertexArray(0)

            GL.glDisable(GL.GL_BLEND)

            GL.glUseProgram(0)

    prochaine_scene = None
    longueur = None
    largeur = None

    def __init__(self):
        self.__cases_possibles = []

        self.programme = creer_programme_shader(
            "shader/damier_vert.glsl", "shader/damier_frag.glsl"
        )
        self.uniform_t = GL.glGetUniformLocation(self.programme, "t")
        self.damier = SceneDamier._GLDamier()
        self.overlay = SceneDamier._GLDamier(True)
        self.pion_test = SceneDamier._GLPion((1, 0))

    def rendre(self, t):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glUseProgram(self.programme)
        GL.glUniform1f(self.uniform_t, t)

        self.damier.rendre()
        self.overlay.rendre()
        self.pion_test.rendre(t, self.longueur, self.largeur)

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
