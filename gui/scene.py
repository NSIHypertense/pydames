from abc import ABC, abstractmethod
import math
import time
import threading
import traceback

import numpy as np
from OpenGL import GL
import imgui

from logic.damier import Pion
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

    GL.glShaderSource(vertex_shader, util.traiter_glsl(util.resource_chemin(vert)))

    GL.glCompileShader(vertex_shader)
    verifier_shader(vertex_shader)

    fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)

    GL.glShaderSource(fragment_shader, util.traiter_glsl(util.resource_chemin(frag)))

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
    def rendre(self, t: float):
        pass

    @abstractmethod
    def fini(self):
        pass


class SceneTitre(Scene):
    prochaine_scene = None
    longueur = None
    largeur = None
    curseur = None
    clic = False

    def __init__(self):
        self.popup_commencer = False
        self.popup_reglages = False

        self.destination = "127.0.0.1"
        self.port = "2332"
        self.connexion = False
        self.connexion_erreur = 0
        self.thread_connexion = None

        self.quitter = False

    def __connecter(self, t):
        def creer_socket():
            try:
                mp.client.arreter()
                mp.client.demarrer(self.destination, int(self.port))
            except OSError:
                print(traceback.format_exc())
                self.connexion = False
                self.connexion_erreur = t + 2

        self.thread_connexion = threading.Thread(target=creer_socket)
        self.thread_connexion.start()

    def rendre(self, t):
        io = imgui.get_io()
        echelle = io.font_global_scale

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

        longueur_bouton = 150 * echelle
        largeur_bouton = 30 * echelle

        imgui.set_cursor_pos_x((longueur - longueur_bouton) / 2)
        if imgui.button("Commencer", longueur_bouton, largeur_bouton):
            self.popup_commencer = True

        imgui.set_cursor_pos_x((longueur - longueur_bouton) / 2)
        if imgui.button("Réglages", longueur_bouton, largeur_bouton):
            self.popup_reglages = True

        imgui.set_cursor_pos_x((longueur - longueur_bouton) / 2)
        if imgui.button("Quitter", longueur_bouton, largeur_bouton):
            self.quitter = True

        imgui.end()

        if self.popup_commencer:
            imgui.open_popup("Commencer")
        if self.popup_reglages:
            imgui.open_popup("Réglages")

        taille_popup = (longueur_fenetre // 2, largeur_fenetre // 4)
        position_popup = (
            (longueur_fenetre - taille_popup[0]) / 2,
            (largeur_fenetre - taille_popup[1]) / 2,
        )

        imgui.set_next_window_size(*taille_popup)
        imgui.set_next_window_position(*position_popup)

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
                        self.prochaine_scene = SceneSalons()
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

                imgui.same_line()
                if imgui.button("Retour"):
                    self.popup_commencer = False
                    imgui.close_current_popup()

        taille_popup = (int(longueur_fenetre / 1.15), largeur_fenetre // 2)
        position_popup = (
            (longueur_fenetre - taille_popup[0]) / 2,
            (largeur_fenetre - taille_popup[1]) / 2,
        )

        imgui.set_next_window_size(*taille_popup)
        imgui.set_next_window_position(*position_popup)

        with imgui.begin_popup_modal(
            "Réglages",
            flags=imgui.WINDOW_NO_MOVE
            | imgui.WINDOW_NO_RESIZE
            | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR,
        ) as popup:
            if popup.opened:
                imgui.internal.push_item_flag(
                    imgui.internal.ITEM_DISABLED, mp.client.reglages.pseudo_force
                )
                imgui.push_style_var(
                    imgui.STYLE_ALPHA,
                    imgui.get_style().alpha
                    * (1 - int(mp.client.reglages.pseudo_force) / 2),
                )

                _, pseudo = imgui.input_text("Pseudonyme", mp.client.reglages.pseudo)
                if 3 <= len(pseudo) <= 24:
                    mp.client.reglages.pseudo = pseudo
                else:
                    imgui.text("Le pseudonyme doit comporter entre 3 et 24 caractères.")

                imgui.pop_style_var()
                imgui.internal.pop_item_flag()

                _, damier_taille = imgui.input_int(
                    "Taille du damier", mp.client.reglages.taille_damier, step=1
                )

                if 4 <= damier_taille <= 32:
                    mp.client.reglages.taille_damier = damier_taille

                _, mp.client.reglages.duree_animation = imgui.input_float(
                    "Durée des animations des pions",
                    mp.client.reglages.duree_animation,
                    step=0.5,
                    step_fast=0.1,
                )

                imgui.text("Couleurs")

                _, mp.client.reglages.couleurs["noir"] = imgui.color_edit3(
                    "Pions noirs", *mp.client.reglages.couleurs["noir"]
                )
                _, mp.client.reglages.couleurs["blanc"] = imgui.color_edit3(
                    "Pions blancs", *mp.client.reglages.couleurs["blanc"]
                )
                _, mp.client.reglages.couleurs["dame_noir"] = imgui.color_edit3(
                    "Dames noires",
                    *mp.client.reglages.couleurs["dame_noir"],
                )
                _, mp.client.reglages.couleurs["dame_blanc"] = imgui.color_edit3(
                    "Dames blanches",
                    *mp.client.reglages.couleurs["dame_blanc"],
                )
                _, mp.client.reglages.couleurs["damier_noir"] = imgui.color_edit3(
                    "Cases noires du damier",
                    *mp.client.reglages.couleurs["damier_noir"],
                )
                _, mp.client.reglages.couleurs["damier_blanc"] = imgui.color_edit3(
                    "Cases blanches du damier",
                    *mp.client.reglages.couleurs["damier_blanc"],
                )
                _, mp.client.reglages.couleurs["bordure"] = imgui.color_edit3(
                    "Bordure du pion sur la souris",
                    *mp.client.reglages.couleurs["bordure"],
                )
                _, mp.client.reglages.couleurs["cases_possibles"] = imgui.color_edit3(
                    "Déplacements proposés",
                    *mp.client.reglages.couleurs["cases_possibles"],
                )
                _, mp.client.reglages.couleurs["cases_deplacements"] = (
                    imgui.color_edit3(
                        "Déplacements de l'adversaire",
                        *mp.client.reglages.couleurs["cases_deplacements"],
                    )
                )

                imgui.dummy(1, 10)

                if imgui.button("Retour"):
                    self.popup_reglages = False
                    imgui.close_current_popup()

    def fini(self):
        pass


class SceneSalons(Scene):
    prochaine_scene = None
    longueur = None
    largeur = None
    curseur = None
    clic = False

    def __init__(self):
        self.code_salon = ""

    def rendre(self, t):
        if not mp.client.sock or mp.client.connexion_erreur:
            self.prochaine_scene = SceneTitre()
            return

        io = imgui.get_io()
        echelle = io.font_global_scale

        longueur_fenetre = io.display_size.x
        largeur_fenetre = io.display_size.y

        longueur_popup = max(int(longueur_fenetre / 2), 450)
        largeur_popup = max(largeur_fenetre // 6, 120)

        imgui.set_next_window_size(longueur_popup, largeur_popup)
        imgui.set_next_window_position(
            (longueur_fenetre - longueur_popup) / 2,
            (largeur_fenetre - largeur_popup) / 2,
        )

        imgui.begin(
            "Salons",
            False,
            imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE,
        )

        _, code_salon = imgui.input_text("Code du salon", self.code_salon)
        if not code_salon:
            imgui.text("Un code aléatoire à 4 chiffres sera généré pour le salon.")
            self.code_salon = code_salon
        elif not (4 <= len(code_salon) <= 32):
            imgui.text("Le code du salon doit comporter entre 4 et 32 caractères.")
        else:
            self.code_salon = code_salon

        texte_confirmer = "Confirmer" if self.code_salon else "Créer"

        imgui.dummy(1, 10)

        longueur = (
            max(
                imgui.calc_text_size(texte_confirmer)[0],
                imgui.calc_text_size("Déconnecter")[0],
            )
            + 20
        )

        imgui.set_cursor_pos_x((longueur_popup - (2 * longueur + 20)) / 2)

        if imgui.button(texte_confirmer, longueur, 30 * echelle):
            mp.client.envoyer(mp.client.paquet_salon(self.code_salon))
            self.prochaine_scene = SceneAttente()

        imgui.same_line(spacing=20)
        if imgui.button("Déconnecter", longueur, 30 * echelle):
            mp.client.arreter()
            self.prochaine_scene = SceneTitre()

        imgui.end()

    def fini(self):
        pass


class SceneAttente(Scene):
    prochaine_scene = None
    longueur = None
    largeur = None
    curseur = None
    clic = False

    def rendre(self, t):
        if not mp.client.sock or mp.client.connexion_erreur:
            self.prochaine_scene = SceneTitre()
            return
        elif mp.client.connexion_succes and not mp.client.attente:
            self.prochaine_scene = SceneDamier()
            return

        io = imgui.get_io()
        echelle = io.font_global_scale

        longueur_fenetre = io.display_size.x
        largeur_fenetre = io.display_size.y

        longueur_popup = max(longueur_fenetre // 2, 400)
        largeur_popup = max(largeur_fenetre // 4, 190)

        imgui.set_next_window_size(longueur_popup, largeur_popup)
        imgui.set_next_window_position(
            (longueur_fenetre - longueur_popup) / 2,
            (largeur_fenetre - largeur_popup) / 2,
        )

        imgui.begin(
            "Attente",
            False,
            imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_MOVE,
        )

        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + 10)

        if mp.client.serveur:
            texte_connexion = f"Connecté en tant que '{mp.client.reglages.pseudo}' à {mp.client.serveur[0]}:{mp.client.serveur[1]}"
            imgui.set_cursor_pos_x(
                (longueur_popup - imgui.calc_text_size(texte_connexion)[0]) / 2
            )
            imgui.text(texte_connexion)

        if mp.client.salon:
            imgui.dummy(1, 10)
            texte_salon = f"Code du salon : '{mp.client.salon}'"
            imgui.set_cursor_pos_x(
                (longueur_popup - imgui.calc_text_size(texte_salon)[0]) / 2
            )
            imgui.text(texte_salon)
            imgui.dummy(1, 10)

        points = "." * (1 + int(t * 2) % 3)
        etat_pret = mp.client.pret

        if etat_pret:
            texte_attente = f"Attente du joueur adversaire{points}"

            imgui.set_cursor_pos_x(
                (longueur_popup - imgui.calc_text_size(texte_attente)[0]) / 2
            )
            imgui.text(texte_attente)

        texte_etat = (
            "Vous êtes prêt." if etat_pret else f"Vous n'êtes pas encore prêt{points}"
        )
        imgui.set_cursor_pos_x(
            (longueur_popup - imgui.calc_text_size(texte_etat)[0]) / 2
        )
        imgui.text(texte_etat)

        imgui.dummy(1, 10)

        longueur_bouton = (
            max(
                imgui.calc_text_size("Prêt")[0],
                imgui.calc_text_size("Déconnecter")[0],
            )
            + 20
        )

        imgui.set_cursor_pos_x((longueur_popup - (longueur_bouton * 2 + 20)) / 2)

        if etat_pret:
            imgui.internal.push_item_flag(imgui.internal.ITEM_DISABLED, True)
            imgui.push_style_var(imgui.STYLE_ALPHA, imgui.get_style().alpha * 0.5)
        if imgui.button("Prêt", longueur_bouton, 30 * echelle):
            mp.client.pret = True
            mp.client.envoyer(mp.client.paquet_pret())
        if etat_pret:
            imgui.pop_style_var()
            imgui.internal.pop_item_flag()

        imgui.same_line(spacing=20)

        if imgui.button("Déconnecter", longueur_bouton, 30 * echelle):
            mp.client.arreter()
            self.prochaine_scene = SceneTitre()

        imgui.end()

    def fini(self):
        pass


class SceneDamier(Scene):
    class _GLDamier:
        def __init__(
            self,
            damier_longueur: int,
            damier_largeur: int,
            damier_overlay: bool,
            inverser: bool,
        ):
            self.longueur, self.largeur, self.damier_overlay, self.inverser = (
                damier_longueur,
                damier_largeur,
                damier_overlay,
                inverser,
            )

            self.programme = creer_programme_shader(
                "shader/damier_vert.glsl", "shader/damier_frag.glsl"
            )
            self.uniform_t = GL.glGetUniformLocation(self.programme, "t")
            self.uniform_fenetre_taille = GL.glGetUniformLocation(
                self.programme, "fenetre_taille"
            )
            self.uniform_fenetre_position = GL.glGetUniformLocation(
                self.programme, "fenetre_position"
            )
            self.uniform_damier_taille = GL.glGetUniformLocation(
                self.programme, "damier_taille"
            )
            self.uniform_damier_curseur = GL.glGetUniformLocation(
                self.programme, "damier_curseur"
            )

            GL.glUseProgram(self.programme)
            GL.glUseProgram(0)

            sommets, couleurs = self.generer_buffers([], [])

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
            self,
            cases_possibles: list[tuple[int, int]],
            cases_deplacements: list[tuple[int, int]],
        ) -> tuple[list[float], list[float]]:
            sommets = []
            couleurs = []
            m = (2 / self.longueur, 2 / self.largeur)

            couleur_damier_noir = mp.client.reglages.couleurs["damier_noir"]
            couleur_damier_blanc = mp.client.reglages.couleurs["damier_blanc"]
            couleur_cases_possibles = mp.client.reglages.couleurs["cases_possibles"]
            couleur_cases_deplacements = mp.client.reglages.couleurs[
                "cases_deplacements"
            ]

            for y in range(self.largeur):
                for x in range(self.longueur):
                    valeur_p, valeur_d = (
                        int((x, y) in cases_possibles),
                        cases_deplacements.index((x, y))
                        if (x, y) in cases_deplacements
                        else -1,
                    )

                    if valeur_d != -1:
                        valeur_d = (
                            1.0 if valeur_d in (0, len(cases_deplacements) - 1) else 0.5
                        )

                    if valeur_p > 0:
                        valeur_d *= 0.25

                    if not self.damier_overlay or valeur_p > 0 or valeur_d > 0:
                        x0 = x * m[0] - 1
                        y0 = (self.largeur - 1 - y) * m[1] - 1
                        x1 = x0 + m[0]
                        y1 = y0 + m[1]

                        _sommets = [x0, y0, 0, x1, y0, 0, x0, y1, 0]
                        _sommets.extend([x1, y0, 0, x1, y1, 0, x0, y1, 0])
                        if self.inverser:
                            _sommets = [-s for s in _sommets]
                        sommets.extend(_sommets)

                        if self.damier_overlay:
                            couleur = [
                                valeur_p * couleur_cases_possibles[i]
                                + valeur_d * couleur_cases_deplacements[i]
                                for i in range(3)
                            ]
                            couleur.append(0.0)
                        else:
                            couleur = (
                                [*couleur_damier_blanc, 1.0]
                                if (x + y) % 2 == 0
                                else [*couleur_damier_noir, 1.0]
                            )

                        couleurs.extend(couleur * 6)

            return sommets, couleurs

        def set_cases(
            self,
            cases_possibles: list[tuple[int, int]],
            cases_deplacements: list[tuple[int, int]],
        ):
            sommets, couleurs = self.generer_buffers(
                cases_possibles, cases_deplacements
            )

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

        def rendre(self, t, position, taille, curseur: tuple[int, int] | None = None):
            if not curseur:
                curseur = (-1, -1)

            GL.glUseProgram(self.programme)
            GL.glUniform1f(self.uniform_t, t)
            GL.glUniform2f(self.uniform_fenetre_taille, *taille)
            GL.glUniform2f(self.uniform_fenetre_position, *position)
            GL.glUniform2f(self.uniform_damier_taille, self.longueur, self.largeur)
            GL.glUniform2f(self.uniform_damier_curseur, *curseur)

            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glBindVertexArray(self.vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.longueur * self.largeur * 6)
            GL.glBindVertexArray(0)
            GL.glDisable(GL.GL_BLEND)

        def fini(self):
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

        def __init__(
            self,
            gl_damier: "SceneDamier._GLDamier",
            x: int,
            y: int,
            type: Pion,
            inverser: bool,
        ):
            (
                self._gl_damier,
                self.t_pre,
                self.position,
                self.position_pre,
                self.position_pre_test,
                self.type,
                self.dame,
                self.inverser,
            ) = (
                gl_damier,
                0.0,
                (x, y),
                (x, y),
                (x, y),
                type,
                False,
                inverser,
            )

            self.programme = creer_programme_shader(
                "shader/pion_vert.glsl", "shader/pion_frag.glsl"
            )
            self.uniform_t = GL.glGetUniformLocation(self.programme, "t")
            self.uniform_t_pre = GL.glGetUniformLocation(self.programme, "t_pre")
            self.uniform_fenetre_taille = GL.glGetUniformLocation(
                self.programme, "fenetre_taille"
            )
            self.uniform_fenetre_position = GL.glGetUniformLocation(
                self.programme, "fenetre_position"
            )
            self.uniform_damier_taille = GL.glGetUniformLocation(
                self.programme, "damier_taille"
            )
            self.uniform_pion_position = GL.glGetUniformLocation(
                self.programme, "pion_position"
            )
            self.uniform_pion_position_pre = GL.glGetUniformLocation(
                self.programme, "pion_position_pre"
            )
            self.uniform_pion_couleur = GL.glGetUniformLocation(
                self.programme, "pion_couleur"
            )
            self.uniform_pion_selection = GL.glGetUniformLocation(
                self.programme, "pion_selection"
            )
            self.uniform_pion_dame = GL.glGetUniformLocation(
                self.programme, "pion_dame"
            )
            self.uniform_duree_animation = GL.glGetUniformLocation(
                self.programme, "duree_animation"
            )
            self.uniform_couleur_noir = GL.glGetUniformLocation(
                self.programme, "couleur_noir"
            )
            self.uniform_couleur_blanc = GL.glGetUniformLocation(
                self.programme, "couleur_blanc"
            )
            self.uniform_couleur_dame_noir = GL.glGetUniformLocation(
                self.programme, "couleur_dame_noir"
            )
            self.uniform_couleur_dame_blanc = GL.glGetUniformLocation(
                self.programme, "couleur_dame_blanc"
            )
            self.uniform_couleur_bordure = GL.glGetUniformLocation(
                self.programme, "couleur_bordure"
            )

            GL.glUseProgram(self.programme)
            GL.glUniform1f(
                self.uniform_duree_animation, mp.client.reglages.duree_animation
            )
            GL.glUniform3f(
                self.uniform_couleur_noir, *mp.client.reglages.couleurs["noir"]
            )
            GL.glUniform3f(
                self.uniform_couleur_blanc, *mp.client.reglages.couleurs["blanc"]
            )
            GL.glUniform3f(
                self.uniform_couleur_dame_noir,
                *mp.client.reglages.couleurs["dame_noir"],
            )
            GL.glUniform3f(
                self.uniform_couleur_dame_blanc,
                *mp.client.reglages.couleurs["dame_blanc"],
            )
            GL.glUniform3f(
                self.uniform_couleur_bordure,
                *mp.client.reglages.couleurs["bordure"],
            )
            GL.glUseProgram(0)

            if not SceneDamier._GLPion.buffer_sommets:
                SceneDamier._GLPion.creer_buffer_sommets()

            self.vao = GL.glGenVertexArrays(1)
            GL.glBindVertexArray(self.vao)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, SceneDamier._GLPion.buffer_sommets)
            GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
            GL.glEnableVertexAttribArray(0)
            GL.glBindVertexArray(0)

        def rendre(self, t, position, taille, selection):
            if self.position != self.position_pre_test:
                self.position_pre = self.position_pre_test
                self.position_pre_test = self.position
                self.t_pre = t + mp.client.reglages.duree_animation

            pion_position, pion_position_pre = self.position, self.position_pre
            if self.inverser:
                pion_position = (
                    self._gl_damier.longueur - pion_position[0] - 1,
                    self._gl_damier.largeur - pion_position[1] - 1,
                )
                pion_position_pre = (
                    self._gl_damier.longueur - pion_position_pre[0] - 1,
                    self._gl_damier.largeur - pion_position_pre[1] - 1,
                )

            GL.glUseProgram(self.programme)

            GL.glUniform1f(self.uniform_t, t)
            GL.glUniform1f(self.uniform_t_pre, self.t_pre)
            GL.glUniform2f(self.uniform_fenetre_taille, *taille)
            GL.glUniform2f(self.uniform_fenetre_position, *position)
            GL.glUniform2f(
                self.uniform_damier_taille,
                self._gl_damier.longueur,
                self._gl_damier.largeur,
            )
            GL.glUniform2f(self.uniform_pion_position, *pion_position)
            GL.glUniform2f(self.uniform_pion_position_pre, *pion_position_pre)
            GL.glUniform1i(self.uniform_pion_couleur, self.type.couleur().value)
            GL.glUniform1i(self.uniform_pion_selection, selection)
            GL.glUniform1i(self.uniform_pion_dame, self.type.est_dame())

            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

            GL.glBindVertexArray(self.vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
            GL.glBindVertexArray(0)

            GL.glDisable(GL.GL_BLEND)

            GL.glUseProgram(0)

    class _GLTchat:
        def __init__(self):
            self.saisie = ""
            self.affichage_input = False
            self.duree_affichage = 10
            self.longueur = 300
            self.largeur = 150
            self.scroll = 0

        def rendre(self, curseur, clic, position):
            io = imgui.get_io()
            echelle = io.font_global_scale
            maintenant = time.time()

            survole = (
                position[0] <= curseur[0] <= position[0] + self.longueur * echelle
                and position[1] <= curseur[1] <= position[1] + self.largeur * echelle
            )

            if imgui.is_key_down(io.key_map[imgui.KEY_ENTER]):
                self.affichage_input = True
            elif imgui.is_key_down(io.key_map[imgui.KEY_ESCAPE]) or (
                clic and not survole
            ):
                self.affichage_input = False

            opacite = 1.0 if self.affichage_input else (0.2 if survole else 0.1)
            flags = (
                imgui.WINDOW_NO_RESIZE
                | imgui.WINDOW_NO_MOVE
                | imgui.WINDOW_NO_COLLAPSE
                | imgui.WINDOW_NO_SCROLLBAR
            )
            if not self.affichage_input:
                flags |= imgui.WINDOW_NO_TITLE_BAR

            imgui.set_next_window_position(*position)
            imgui.set_next_window_size(self.longueur * echelle, self.largeur * echelle)

            imgui.push_style_var(imgui.STYLE_ALPHA, opacite)
            imgui.begin("Tchat", False, flags)
            imgui.pop_style_var()

            largeur_saisie = 25
            imgui.set_cursor_pos_y((self.largeur - largeur_saisie) * echelle)

            if self.affichage_input:
                self.scroll = max(self.scroll + io.mouse_wheel * 8, 0)

                imgui.set_keyboard_focus_here()
                pressed_enter, self.saisie = imgui.input_text(
                    "##saisie",
                    self.saisie,
                    flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE,
                )

                texte = self.saisie.strip()
                if pressed_enter and texte and len(texte) <= 300:
                    mp.client.envoyer(mp.client.paquet_tchat(texte))
                    self.saisie = ""
                    self.affichage_input = False
            else:
                self.scroll = 0
                if imgui.invisible_button(
                    "##tchat_clic", self.longueur, largeur_saisie
                ):
                    self.affichage_input = True

            messages = [
                m
                for m in mp.client.messages
                if self.affichage_input or (maintenant - m.t < self.duree_affichage)
            ]
            messages = list(reversed(messages))

            y = (self.largeur + self.scroll - 5) * echelle
            if self.affichage_input:
                y -= largeur_saisie * echelle

            for message in messages:
                texte = f"{message.pseudo} : {message.texte}"
                hauteur_ligne = (
                    imgui.calc_text_size(
                        texte, wrap_width=self.longueur * echelle - 10
                    )[1]
                    + 2
                )

                y -= hauteur_ligne
                if y < 0 or y > self.largeur * echelle - largeur_saisie - 2:
                    continue

                imgui.set_cursor_pos_y(y)
                alpha = (
                    1.0
                    if self.affichage_input
                    else max(0.0, 1.0 - (maintenant - message.t) / self.duree_affichage)
                )
                imgui.push_style_var(imgui.STYLE_ALPHA, alpha)
                imgui.text_wrapped(texte)
                imgui.pop_style_var()

            imgui.end()

    class _GLStatut:
        def __init__(self, scene: "SceneDamier"):
            self.scene = scene

        def rendre(self, longueur, largeur):
            io = imgui.get_io()
            echelle = io.font_global_scale

            rendu_taille = (
                125 * echelle,
                (50 + (45 if mp.client.tour else 0)) * echelle,
            )
            imgui.set_next_window_size(*rendu_taille)
            imgui.set_next_window_position(
                longueur - rendu_taille[0], largeur - rendu_taille[1]
            )

            titre = "À votre tour" if mp.client.tour else "##statut"
            flags = (
                imgui.WINDOW_NO_MOVE
                | imgui.WINDOW_NO_RESIZE
                | imgui.WINDOW_NO_COLLAPSE
                | imgui.WINDOW_NO_SCROLLBAR
            )
            if not mp.client.tour:
                flags |= imgui.WINDOW_NO_TITLE_BAR
            imgui.begin(titre, flags=flags)

            texte = mp.client.reglages.pseudo
            taille_texte = imgui.calc_text_size(texte)
            imgui.set_cursor_pos_x((rendu_taille[0] - taille_texte[0]) / 2)

            imgui.text(texte)

            if mp.client.tour:
                texte = "Annuler"
                taille_texte = imgui.calc_text_size(texte)
                imgui.set_cursor_pos_x((rendu_taille[0] - taille_texte[0]) / 2 - 2)

                if imgui.button(texte):
                    mp.client.tour = False
                    self.scene.__cases_possibles = []
                    self.scene.overlay.set_cases(
                        self.__cases_possibles, self.__cases_deplacements
                    )
                    mp.client.envoyer(mp.client.paquet_annuler())

            texte = "Déconnecter"
            taille_texte = imgui.calc_text_size(texte)
            imgui.set_cursor_pos_x((rendu_taille[0] - taille_texte[0]) / 2 - 2)

            if imgui.button(texte):
                mp.client.arreter()
                self.scene.prochaine_scene = SceneTitre()

            imgui.end()

    prochaine_scene = None
    longueur = None
    largeur = None
    curseur = None
    clic = False

    def __init__(self):
        self.__cases_possibles = []
        self.__cases_deplacements = []

        self.damier = SceneDamier._GLDamier(8, 8, False, False)
        self.overlay = SceneDamier._GLDamier(8, 8, True, False)
        self.pions = []
        self.tchat = SceneDamier._GLTchat()
        self.statut = SceneDamier._GLStatut(self)
        self.clic_avant = False
        self.appui = False
        self.pion_curseur = None

    def __trouver_cases_deplacements(
        self, a: tuple[int, int], b: tuple[int, int]
    ) -> list[tuple[int, int]]:
        cases = self.__cases_deplacements

        if a:
            cases.append(a)

            if b:
                xa, ya = a
                xb, yb = b

                for i in range(1, abs(xa - xb)):
                    x = xa + (i if (xb - xa) > 0 else -i)
                    y = ya + (i if (yb - ya) > 0 else -i)
                    cases.append((x, y))

                cases.append(b)

        cases = list(dict.fromkeys(cases))
        return cases

    def rendre(self, t):
        if not mp.client.sock or mp.client.connexion_erreur:
            self.prochaine_scene = SceneTitre()
            return
        elif mp.client.attente:
            self.prochaine_scene = SceneAttente()
            return

        io = imgui.get_io()
        echelle = io.font_global_scale

        rendu_taille = min(self.longueur, self.largeur)
        rendu_position = (
            (self.longueur - rendu_taille) // 2,
            (self.largeur - rendu_taille) // 2,
        )
        rendu_taille = (rendu_taille, rendu_taille)

        damier_curseur = (
            (self.curseur[0] - rendu_position[0])
            * self.damier.longueur
            // rendu_taille[0],
            (self.curseur[1] - rendu_position[1])
            * self.damier.largeur
            // rendu_taille[1],
        )

        inverser = mp.client.couleur == Pion.BLANC
        if self.damier.inverser != inverser:
            self.damier.inverser, self.overlay.inverser = inverser, inverser
            for p in self.pions:
                p.inverser = inverser
            self.damier.set_cases([], [])
            self.overlay.set_cases(self.__cases_possibles, self.__cases_deplacements)

        self.appui = not self.clic and self.clic_avant and mp.client.tour
        self.clic_avant = self.clic

        if (
            mp.client.damier
            and mp.client.damier.longueur != self.damier.longueur
            and mp.client.damier.largeur != self.damier.largeur
        ):
            taille_damier = (
                mp.client.damier.longueur,
                mp.client.damier.largeur,
            )
            self.damier.longueur, self.damier.largeur = taille_damier
            self.overlay.longueur, self.overlay.largeur = taille_damier
            self.damier.set_cases([], [])
            self.overlay.set_cases(self.__cases_possibles, self.__cases_deplacements)

        while mp.client.deplacements:
            self.__cases_possibles = []
            self.overlay.set_cases(self.__cases_possibles, self.__cases_deplacements)

            source, cible = mp.client.deplacements.pop(0), mp.client.deplacements.pop(0)

            pion = next((p for p in self.pions if p.position == source), None)

            if pion:
                pion.type = mp.client.damier.obtenir_pion(*cible)
                assert pion.type
                if pion.type.couleur() != mp.client.couleur:
                    self.__cases_deplacements = self.__trouver_cases_deplacements(
                        source, cible
                    )
                pion.position = cible
            else:
                print("impossible d'effectuer le déplacement !")

            self.overlay.set_cases(self.__cases_possibles, self.__cases_deplacements)

        while mp.client.sauts:
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
                        self.pions.append(
                            SceneDamier._GLPion(self.damier, x, y, c, inverser)
                        )

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        GL.glViewport(*rendu_position, *rendu_taille)

        self.damier.rendre(
            t, rendu_position, rendu_taille, damier_curseur if mp.client.tour else None
        )
        if mp.client.tour:
            self.overlay.rendre(t, rendu_position, rendu_taille)

        if mp.client.selection:
            self.pion_curseur = mp.client.selection
            self.__cases_possibles = [
                c
                for c in mp.client.damier.trouver_cases_possibles(*mp.client.selection)
                if len(mp.client.damier.deplacer_pion(self.pion_curseur, c, False)) > 0
            ]
            self.overlay.set_cases(self.__cases_possibles, self.__cases_deplacements)

        if inverser:
            damier_curseur = (
                self.damier.longueur - damier_curseur[0] - 1,
                self.damier.largeur - damier_curseur[1] - 1,
            )

        selection_est_pion = (
            bool(mp.client.damier)
            and 0 <= damier_curseur[0] < mp.client.damier.longueur
            and 0 <= damier_curseur[1] < mp.client.damier.largeur
            and mp.client.damier.obtenir_pion(*damier_curseur)
        )

        if (
            not selection_est_pion
            and self.appui
            and damier_curseur in self.__cases_possibles
        ):
            self.__cases_possibles, self.__cases_deplacements = [], []
            self.overlay.set_cases(self.__cases_possibles, self.__cases_deplacements)

            mp.client.envoyer(
                mp.client.paquet_deplacer(self.pion_curseur, damier_curseur)
            )

        for pion in self.pions:
            if mp.client.selection:
                pion.rendre(t, rendu_position, rendu_taille, False)
            else:
                selection = (
                    mp.client.tour
                    and selection_est_pion
                    and pion.type.couleur() == mp.client.couleur
                    and damier_curseur[0] == pion.position[0]
                    and damier_curseur[1] == pion.position[1]
                ) or False

                if selection and self.appui:
                    self.pion_curseur = damier_curseur
                    self.__cases_possibles = mp.client.damier.trouver_cases_possibles(
                        *pion.position
                    )
                    self.overlay.set_cases(
                        self.__cases_possibles,
                        self.__cases_deplacements,
                    )

                pion.rendre(t, rendu_position, rendu_taille, selection)

        GL.glUseProgram(0)

        self.statut.rendre(self.longueur, self.largeur)

        self.tchat.rendre(
            self.curseur,
            self.clic,
            (0, self.largeur - self.tchat.largeur * echelle),
        )

    def fini(self):
        self.damier.fini()
