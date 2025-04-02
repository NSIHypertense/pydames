from enum import Enum

DAMIER_LONGUEUR = 8
DAMIER_LARGEUR = 8


class CouleurPion(Enum):
    NOIR = 1
    BLANC = 2


class Damier:
    def __init__(self, longueur: int, largeur: int):
        self.__longueur, self.__largeur = longueur, largeur
        self.vider()

    def from_matrice(matrice: list[list[CouleurPion | int | None]]) -> "Damier":
        assert matrice != [] and matrice[0] != []

        longueur, largeur = len(matrice), len(matrice[0])
        damier = Damier(longueur, largeur)

        for x in range(longueur):
            assert len(matrice[x]) == largeur
            for y in range(largeur):
                valeur = matrice[x][y]
                if isinstance(valeur, int):
                    valeur = CouleurPion(valeur)
                assert not valeur or isinstance(valeur, CouleurPion)
                damier.__matrice[x][y] = valeur

        return damier

    @property
    def longueur(self) -> int:
        return self.__longueur

    @property
    def largeur(self) -> int:
        return self.__largeur

    @property
    def matrice(self) -> list[list[CouleurPion | None]]:
        return [rang.copy() for rang in self.__matrice]  # copie de liste 2D

    def vider(self):
        self.__matrice = [
            [None for _ in range(self.__largeur)] for _ in range(self.__longueur)
        ]

    def installer(self):
        n = self.__largeur // 2 - 1

        for y in range(0, n):
            for x in range((y + 1) % 2, self.__longueur, 2):
                self.__matrice[x][y] = CouleurPion.NOIR
        for y in range(self.__largeur - n, self.__largeur):
            for x in range((y + 1) % 2, self.__longueur, 2):
                self.__matrice[x][y] = CouleurPion.BLANC

    def obtenir_pion(self, x: int, y: int) -> CouleurPion | None:
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur
        return self.__matrice[x][y]

    def ajouter_pion(self, x: int, y: int, couleur: CouleurPion):
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur
        self.__matrice[x][y] = couleur

    def enlever_pion(self, x: int, y: int):
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur
        self.__matrice[x][y] = None

    def deplacer_pion(
        self, position_source: tuple[int, int], position_cible: tuple[int, int]
    ) -> tuple[int, int] | None:
        case_sautee = None

        x_src, y_src = position_source
        x_dst, y_dst = position_cible

        assert 0 <= x_src < self.__longueur and 0 <= y_src < self.__largeur
        assert self.__matrice[x_src][y_src] is not None
        assert 0 <= x_dst < self.__longueur and 0 <= y_dst < self.__largeur

        if abs(x_dst - x_src) == 2 and abs(y_dst - y_src) == 2:
            x_inter = (x_src + x_dst) // 2
            y_inter = (y_src + y_dst) // 2

            if self.__matrice[x_inter][y_inter] is not None:
                case_sautee = (x_inter, y_inter)
                self.enlever_pion(x_inter, y_inter)

        self.__matrice[x_dst][y_dst] = self.__matrice[x_src][y_src]
        self.__matrice[x_src][y_src] = None

        return case_sautee

    def trouver_cases_possibles(self, x: int, y: int) -> list[tuple[int, int]]:
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur

        cases = []
        couleur = self.__matrice[x][y]
        if not couleur:
            return cases

        direction = 1 if couleur == CouleurPion.NOIR else -1

        for dx in [-1, 1]:
            nx, ny = x + dx, y + direction

            if (
                0 <= nx < self.__longueur
                and 0 <= ny < self.__largeur
                and self.__matrice[nx][ny] is None
            ):
                cases.append((nx, ny))

            nx, ny = x + 2 * dx, y + 2 * direction

            if 0 <= nx < self.__longueur and 0 <= ny < self.__largeur:
                pion_inter = self.__matrice[x + dx][y + direction]
                if (
                    pion_inter is not None
                    and pion_inter != couleur
                    and self.__matrice[nx][ny] is None
                ):
                    cases.append((nx, ny))

        return cases

    def gagnant(self) -> CouleurPion | None:
        pions_noirs = any(
            self.__matrice[x][y] == CouleurPion.NOIR
            for x in range(self.__longueur)
            for y in range(self.__largeur)
        )

        pions_blancs = any(
            self.__matrice[x][y] == CouleurPion.BLANC
            for x in range(self.__longueur)
            for y in range(self.__largeur)
        )

        if not pions_noirs:
            return CouleurPion.BLANC
        if not pions_blancs:
            return CouleurPion.NOIR

        return None

    def est_bloque(self) -> bool:
        noir_peut_jouer = any(
            self.trouver_cases_possibles(x, y)
            for x in range(self.__longueur)
            for y in range(self.__largeur)
            if self.__matrice[x][y] == CouleurPion.NOIR
        )

        blanc_peut_jouer = any(
            self.trouver_cases_possibles(x, y)
            for x in range(self.__longueur)
            for y in range(self.__largeur)
            if self.__matrice[x][y] == CouleurPion.BLANC
        )

        return not blanc_peut_jouer and not noir_peut_jouer
