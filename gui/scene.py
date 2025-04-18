from abc import ABC, abstractmethod
import math
import threading
import traceback

import numpy as np
from OpenGL import GL
import imgui

from logic.damier import Pion, DAMIER_LARGEUR, DAMIER_LONGUEUR
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

        imgui.set_next_window_size(*taille_popup)
        imgui.set_next_window_position(*position_popup)

        with imgui.begin_popup_modal(
            "Réglages", flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE
        ) as popup:
            if popup.opened:
                _, pseudo = imgui.input_text("Pseudonyme", mp.client.pseudo)
                if 3 <= len(pseudo) <= 24:
                    mp.client.pseudo = pseudo
                else:
                    imgui.text("Le pseudonyme doit comporter entre 3 et 24 caractères.")

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
        io = imgui.get_io()
        echelle = io.font_global_scale

        longueur_fenetre = io.display_size.x
        largeur_fenetre = io.display_size.y

        longueur_popup = max(int(longueur_fenetre / 2), 500)
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

        imgui.dummy(1, 10)

        longueur = (
            max(
                imgui.calc_text_size("Confirmer")[0],
                imgui.calc_text_size("Déconnecter")[0],
            )
            + 20
        )

        imgui.set_cursor_pos_x((longueur_popup - (2 * longueur + 20)) / 2)

        if imgui.button("Confirmer", longueur, 30 * echelle):
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
        if mp.client.connexion_erreur:
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
        largeur_popup = max(largeur_fenetre // 4, 180)

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
            texte_connexion = f"Connecté en tant que '{mp.client.pseudo}' à {mp.client.serveur[0]}:{mp.client.serveur[1]}"
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
        def __init__(self, damier_overlay: bool = False):
            self.damier_overlay = damier_overlay

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

            GL.glUseProgram(self.programme)
            GL.glUniform2f(self.uniform_damier_taille, DAMIER_LONGUEUR, DAMIER_LARGEUR)
            GL.glUseProgram(0)

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

            for y in range(DAMIER_LARGEUR):
                for x in range(DAMIER_LONGUEUR):
                    if not self.damier_overlay or (x, y) in cases_possibles:
                        x0 = x * mx - 1
                        y0 = (DAMIER_LARGEUR - 1 - y) * my - 1
                        x1 = x0 + mx
                        y1 = y0 + my

                        sommets.extend([x0, y0, 0, x1, y0, 0, x0, y1, 0])
                        sommets.extend([x1, y0, 0, x1, y1, 0, x0, y1, 0])

                        if self.damier_overlay:
                            couleur = [1, 0, 1, 0]
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

        def rendre(self, t, position, taille):
            GL.glUseProgram(self.programme)
            GL.glUniform1f(self.uniform_t, t)
            GL.glUniform2f(self.uniform_fenetre_taille, *taille)
            GL.glUniform2f(self.uniform_fenetre_position, *position)

            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glBindVertexArray(self.vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, DAMIER_LONGUEUR * DAMIER_LARGEUR * 6)
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

        def __init__(self, x: int, y: int, type: Pion):
            self.position, self.type, self.dame = (x, y), type, False

            self.programme = creer_programme_shader(
                "shader/pion_vert.glsl", "shader/pion_frag.glsl"
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
            self.uniform_pion_position = GL.glGetUniformLocation(
                self.programme, "pion_position"
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

        def rendre(self, t, position, taille, selection):
            GL.glUseProgram(self.programme)

            GL.glUniform1f(self.uniform_t, t)
            GL.glUniform2f(self.uniform_fenetre_taille, *taille)
            GL.glUniform2f(self.uniform_fenetre_position, *position)
            GL.glUniform2f(self.uniform_pion_position, *self.position)
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

    prochaine_scene = None
    longueur = None
    largeur = None
    curseur = None
    clic = False

    def __init__(self):
        self.__cases_possibles = []

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
        elif mp.client.attente:
            self.prochaine_scene = SceneAttente()
            return

        io = imgui.get_io()
        echelle = io.font_global_scale

        self.appui = not self.clic and self.clic_avant and mp.client.tour
        self.clic_avant = self.clic

        while mp.client.deplacements:
            self.__cases_possibles = []
            self.overlay.set_cases([])

            source, cible = mp.client.deplacements.pop(0), mp.client.deplacements.pop(0)
            pion = next((p for p in self.pions if p.position == source), None)

            if pion:
                pion.type = mp.client.damier.obtenir_pion(*cible)
                assert pion.type
                pion.position = cible
            else:
                print("impossible d'effectuer le déplacement !")

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
                        self.pions.append(SceneDamier._GLPion(x, y, c))

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        rendu_taille = min(self.longueur, self.largeur)
        rendu_position = (
            (self.longueur - rendu_taille) // 2,
            (self.largeur - rendu_taille) // 2,
        )
        rendu_taille = (rendu_taille, rendu_taille)
        GL.glViewport(*rendu_position, *rendu_taille)

        self.damier.rendre(t, rendu_position, rendu_taille)
        self.overlay.rendre(t, rendu_position, rendu_taille)

        if mp.client.selection:
            self.pion_curseur = mp.client.selection
            self.__cases_possibles = [
                c
                for c in mp.client.damier.trouver_cases_possibles(*mp.client.selection)
                if len(mp.client.damier.deplacer_pion(self.pion_curseur, c, False)) > 0
            ]
            self.overlay.set_cases(self.__cases_possibles)

        damier_curseur = (
            (self.curseur[0] - rendu_position[0]) * DAMIER_LONGUEUR // rendu_taille[0],
            (self.curseur[1] - rendu_position[1]) * DAMIER_LARGEUR // rendu_taille[1],
        )

        selection_est_pion = (
            bool(mp.client.damier)
            and 0 <= damier_curseur[0] < DAMIER_LONGUEUR
            and 0 <= damier_curseur[1] < DAMIER_LARGEUR
            and mp.client.damier.obtenir_pion(*damier_curseur)
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
            if mp.client.selection:
                pion.rendre(t, rendu_position, rendu_taille, False)
            else:
                selection = (
                    selection_est_pion
                    and pion.type.couleur() == mp.client.couleur
                    and damier_curseur[0] == pion.position[0]
                    and damier_curseur[1] == pion.position[1]
                ) or False

                if selection and self.appui:
                    self.pion_curseur = damier_curseur
                    self.__cases_possibles = mp.client.damier.trouver_cases_possibles(
                        *pion.position
                    )
                    self.overlay.set_cases(self.__cases_possibles)

                pion.rendre(t, rendu_position, rendu_taille, selection)

        GL.glUseProgram(0)

        rendu_taille = (125 * echelle, (80 if mp.client.tour else 35) * echelle)
        imgui.set_next_window_size(*rendu_taille)
        imgui.set_next_window_position(
            self.longueur - rendu_taille[0], self.largeur - rendu_taille[1]
        )

        titre = "À votre tour" if mp.client.tour else "##statut"
        flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE
        if not mp.client.tour:
            flags |= imgui.WINDOW_NO_TITLE_BAR
        imgui.begin(titre, flags=flags)

        if mp.client.tour:
            texte = "Annuler"
            taille_texte = imgui.calc_text_size(texte)

            imgui.set_cursor_pos_x((rendu_taille[0] - taille_texte[0]) / 2 - 2)

            if imgui.button(texte):
                mp.client.tour = False
                self.__cases_possibles = []
                self.overlay.set_cases(self.__cases_possibles)
                mp.client.envoyer(mp.client.paquet_annuler())

        texte = "Déconnecter"
        taille_texte = imgui.calc_text_size(texte)

        imgui.set_cursor_pos_x((rendu_taille[0] - taille_texte[0]) / 2 - 2)

        if imgui.button(texte):
            mp.client.arreter()
            self.prochaine_scene = SceneTitre()

        imgui.end()

    def fini(self):
        self.damier.fini()
