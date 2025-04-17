from enum import Enum

DAMIER_LONGUEUR = 8
DAMIER_LARGEUR = 8


class Pion(Enum):
    NOIR = 1
    BLANC = 2
    DAME_NOIR = 3
    DAME_BLANC = 4

    def couleur(self):
        match self:
            case Pion.NOIR:
                return Pion.NOIR
            case Pion.BLANC:
                return Pion.BLANC
            case Pion.DAME_NOIR:
                return Pion.NOIR
            case Pion.DAME_BLANC:
                return Pion.BLANC
            case _:
                raise NotImplementedError("pion inconnu")

    def dame(self):
        match self:
            case Pion.NOIR:
                return Pion.DAME_NOIR
            case Pion.BLANC:
                return Pion.DAME_BLANC
            case Pion.DAME_NOIR:
                return Pion.DAME_NOIR
            case Pion.DAME_BLANC:
                return Pion.DAME_BLANC
            case _:
                raise NotImplementedError("pion inconnu")

    def est_dame(self):
        return self.dame() == self


class Damier:
    def __init__(self, longueur: int, largeur: int):
        self.__longueur, self.__largeur = longueur, largeur
        self.vider()

    def __str__(self):
        matrice_transposee = list(map(list, zip(*self.__matrice)))
        s = ""
        for i in range(len(matrice_transposee)):
            s += str([p.value if p else 0 for p in matrice_transposee[i]]) + "\n"
        s += "\n"
        return s

    def from_matrice(matrice: list[list[Pion | int | None]]) -> "Damier":
        assert matrice != [] and matrice[0] != []

        longueur, largeur = len(matrice), len(matrice[0])
        damier = Damier(longueur, largeur)

        for x in range(longueur):
            assert len(matrice[x]) == largeur
            for y in range(largeur):
                valeur = matrice[x][y]
                if isinstance(valeur, int):
                    valeur = Pion(valeur)
                assert not valeur or isinstance(valeur, Pion)
                damier.__matrice[x][y] = valeur

        return damier

    @property
    def longueur(self) -> int:
        return self.__longueur

    @property
    def largeur(self) -> int:
        return self.__largeur

    @property
    def matrice(self) -> list[list[Pion | None]]:
        return [rang.copy() for rang in self.__matrice]  # copie de liste 2D

    def vider(self):
        self.__matrice = [
            [None for _ in range(self.__largeur)] for _ in range(self.__longueur)
        ]

    def installer(self):
        n = self.__largeur // 2 - 1

        for y in range(0, n):
            for x in range((y + 1) % 2, self.__longueur, 2):
                self.__matrice[x][y] = Pion.NOIR
        for y in range(self.__largeur - n, self.__largeur):
            for x in range((y + 1) % 2, self.__longueur, 2):
                self.__matrice[x][y] = Pion.BLANC

    def obtenir_pion(self, x: int, y: int) -> Pion | None:
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur
        return self.__matrice[x][y]

    def ajouter_pion(self, x: int, y: int, couleur: Pion):
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur
        self.__matrice[x][y] = couleur

    def enlever_pion(self, x: int, y: int):
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur
        self.__matrice[x][y] = None

    def deplacer_pion(
        self,
        position_source: tuple[int, int],
        position_cible: tuple[int, int],
        effectuer: bool = True,
    ) -> list[tuple[int, int]]:
        cases_sautees = []

        x_src, y_src = position_source
        x_dst, y_dst = position_cible

        assert 0 <= x_src < self.__longueur and 0 <= y_src < self.__largeur
        assert self.__matrice[x_src][y_src]
        assert 0 <= x_dst < self.__longueur and 0 <= y_dst < self.__largeur

        d = x_dst - x_src
        assert abs(d) == abs(y_dst - y_src)

        pion = self.__matrice[x_src][y_src]

        for dx in range(0, d, 1 if d > 0 else -1):
            dy = dx if (y_dst - y_src) > 0 else -dx
            if d < 0:
                dy = -dy
            n = (x_src + dx, y_src + dy)

            if 0 <= n[1] < self.__largeur:
                if self.__matrice[n[0]][n[1]]:
                    if n[0] != x_src and n[1] != y_src:
                        cases_sautees.append(n)
                    if effectuer:
                        self.__matrice[n[0]][n[1]] = None

        modification_dame = (pion == Pion.NOIR and y_dst == self.__largeur - 1) or (
            pion == Pion.BLANC and y_dst == 0
        )

        if effectuer:
            if modification_dame:
                pion = pion.dame()
            self.__matrice[x_dst][y_dst] = pion

        return cases_sautees

    def trouver_cases_possibles(self, x: int, y: int) -> list[tuple[int, int]]:
        assert 0 <= x < self.__longueur and 0 <= y < self.__largeur

        cases = []
        pion = self.__matrice[x][y]
        if not pion:
            return cases

        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        max_distance = max(self.__longueur, self.__largeur) if pion.est_dame() else 2
        avance = 1 if pion.couleur() == Pion.NOIR else -1

        for d in directions:
            if not pion.est_dame() and d[1] != avance:
                continue

            for dist in range(1, max_distance):
                n = (x + d[0] * dist, y + d[1] * dist)

                if not (0 <= n[0] < self.__longueur and 0 <= n[1] < self.__largeur):
                    break

                case = self.__matrice[n[0]][n[1]]
                if case:
                    if pion.couleur() != case.couleur():
                        saut = (n[0] + d[0], n[1] + d[1])
                        if (
                            0 <= saut[0] < self.__longueur
                            and 0 <= saut[1] < self.__largeur
                            and not self.__matrice[saut[0]][saut[1]]
                        ):
                            cases.append(saut)
                else:
                    if pion.est_dame() or dist == 1:
                        cases.append(n)

        return cases

    def gagnant(self) -> Pion | None:
        pions_noirs = any(
            self.__matrice[x][y] and self.__matrice[x][y].couleur() == Pion.NOIR
            for x in range(self.__longueur)
            for y in range(self.__largeur)
        )

        pions_blancs = any(
            self.__matrice[x][y] and self.__matrice[x][y].couleur() == Pion.BLANC
            for x in range(self.__longueur)
            for y in range(self.__largeur)
        )

        if not pions_noirs:
            return Pion.BLANC
        if not pions_blancs:
            return Pion.NOIR

        return None

    def est_bloque(self) -> bool:
        noir_peut_jouer = any(
            self.trouver_cases_possibles(x, y)
            for x in range(self.__longueur)
            for y in range(self.__largeur)
            if self.__matrice[x][y] and self.__matrice[x][y].couleur() == Pion.NOIR
        )

        blanc_peut_jouer = any(
            self.trouver_cases_possibles(x, y)
            for x in range(self.__longueur)
            for y in range(self.__largeur)
            if self.__matrice[x][y] and self.__matrice[x][y].couleur() == Pion.BLANC
        )

        return not blanc_peut_jouer and not noir_peut_jouer
