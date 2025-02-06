class Pion:
    def __init__(self, damier, couleur, position):
        """La variable couleur vaut 1 ou -1, et position est un couple de variables."""
         
        self.couleur = couleur
        self.position = position
        self.damier = damier
        self.damier.plateau[self.position[0]][self.position[1]] = self.couleur
        self.etat = True