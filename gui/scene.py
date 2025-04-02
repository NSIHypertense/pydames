from abc import ABC, abstractmethod
import math
import threading
import traceback

import numpy as np
from OpenGL import GL
import imgui

from logic.damier import CouleurPion, DAMIER_LARGEUR, DAMIER_LONGUEUR
import mp.client
import util


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
    def curseur(self) -> tuple[int, int]:
        pass

    @curseur.setter
    @abstractmethod
    def curseur(self, position: tuple[int, int]):
        pass

    @property
    @abstractmethod
    def clic(self) -> bool:
        pass

    @clic.setter
    @abstractmethod
    def clic(self, x: bool):
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
    curseur = None
    clic = False

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

            sommets, couleurs = self.generer_buffers([])

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
                            couleur = (
                                [1 - 1 / 12, 1 - 1 / 12, 1 - 1 / 16, 1]
                                if (x + y) % 2 == 0
                                else [1 / 24, 1 / 24, 1 / 20, 1]
                            )

                        couleurs.extend(couleur * 6)

            return sommets, couleurs

        def set_cases(self, cases_possibles: list[tuple[int, int]]):
            sommets, couleurs = self.generer_buffers(cases_possibles)

            couleurs = np.array(couleurs, dtype=np.float32)
            sommets = np.array(sommets, dtype=np.float32)

            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_couleurs)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER, couleurs.nbytes, couleurs, GL.GL_DYNAMIC_DRAW
            )
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.buffer_sommets)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER, sommets.nbytes, sommets, GL.GL_DYNAMIC_DRAW
            )

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

        def __init__(self, x: int, y: int, couleur: CouleurPion):
            self.position, self.couleur = (x, y), couleur.value

            self.programme = creer_programme_shader(
                "shader/pion_vert.glsl", "shader/pion_frag.glsl"
            )
            self.uniform_t = GL.glGetUniformLocation(self.programme, "t")
            self.uniform_fenetre_taille = GL.glGetUniformLocation(
                self.programme, "fenetre_taille"
            )
            self.uniform_damier_taille = GL.glGetUniformLocation(
                self.programme, "damier_taille"
            )
            self.uniform_pion_position = GL.glGetUniformLocation(
                self.programme, "pion_position"
            )
            self.uniform_pion_couleur = GL.glGetUniformLocation(
                self.programme, "pion_couleur"
            )
            self.uniform_pion_selection = GL.glGetUniformLocation(
                self.programme, "pion_selection"
            )

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

        def rendre(self, t, longueur, largeur, selection):
            GL.glUseProgram(self.programme)

            GL.glUniform1f(self.uniform_t, t)
            GL.glUniform2f(self.uniform_pion_position, *self.position)
            GL.glUniform1i(self.uniform_pion_couleur, self.couleur)
            GL.glUniform1i(self.uniform_pion_selection, selection)
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
    curseur = None
    clic = False

    def __init__(self):
        self.__cases_possibles = []

        self.programme = creer_programme_shader(
            "shader/damier_vert.glsl", "shader/damier_frag.glsl"
        )
        self.uniform_t = GL.glGetUniformLocation(self.programme, "t")
        self.damier = SceneDamier._GLDamier()
        self.overlay = SceneDamier._GLDamier(True)
        self.pions = []
        self.clic_avant = False
        self.appui = False
        self.pion_curseur = None

    def rendre(self, t):
        if not mp.client.sock:
            self.prochaine_scene = SceneTitre()
            return

        self.appui = not self.clic and self.clic_avant and mp.client.tour
        self.clic_avant = self.clic

        while mp.client.deplacements != []:
            self.__cases_possibles = []
            self.overlay.set_cases([])

            source, cible = mp.client.deplacements.pop(0), mp.client.deplacements.pop(0)
            pion = next((p for p in self.pions if p.position == source), None)

            if pion:
                pion.position = cible
            else:
                print("impossible d'effectuer le déplacement !")

        while mp.client.sauts != []:
            case = mp.client.sauts.pop(0)
            i = next((i for i, p in enumerate(self.pions) if p.position == case), None)

            if i is not None:
                del self.pions[i]
            else:
                print("impossible d'effectuer le saut !")

        if self.pions == [] and mp.client.damier:
            m = mp.client.damier.matrice
            for x in range(mp.client.damier.longueur):
                for y in range(mp.client.damier.largeur):
                    c = m[x][y]
                    if c:
                        self.pions.append(SceneDamier._GLPion(x, y, c))

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glUseProgram(self.programme)
        GL.glUniform1f(self.uniform_t, t)

        self.damier.rendre()
        self.overlay.rendre()

        damier_curseur = (
            self.curseur[0] * DAMIER_LONGUEUR // self.longueur,
            self.curseur[1] * DAMIER_LARGEUR // self.largeur,
        )
        selection_est_pion = (
            mp.client.damier is not None
            and mp.client.damier.obtenir_pion(*damier_curseur) is not None
        )

        if (
            not selection_est_pion
            and self.appui
            and damier_curseur in self.__cases_possibles
        ):
            mp.client.envoyer(
                mp.client.paquet_deplacer(self.pion_curseur, damier_curseur)
            )

        for pion in self.pions:
            selection = (
                selection_est_pion
                and pion.couleur == mp.client.couleur.value
                and damier_curseur[0] == pion.position[0]
                and damier_curseur[1] == pion.position[1]
            )

            if selection and self.appui:
                self.pion_curseur = damier_curseur
                self.__cases_possibles = sorted(
                    mp.client.damier.trouver_cases_possibles(*pion.position)
                )
                print(self.__cases_possibles)
                self.overlay.set_cases(self.__cases_possibles.copy())

            pion.rendre(t, self.longueur, self.largeur, selection)

        GL.glUseProgram(0)

    @property
    def cases_possibles(self):
        return self.__cases_possibles
