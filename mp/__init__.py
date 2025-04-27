# Module du multijoueur
from enum import Enum
from abc import ABC, abstractmethod

import ormsgpack


class PaquetClientType(Enum):
    HANDSHAKE = 1
    SALON = 2
    PRET = 3
    DEPLACER = 4
    ANNULER = 5
    TCHAT = 6
    CAPTURE = 7


class PaquetServeurType(Enum):
    HANDSHAKE = 1
    ERREUR = 2
    SALON = 3
    ATTENTE = 4
    LANCEMENT = 5
    CONCLUSION = 6
    COULEUR = 7
    DEPLACEMENTS = 8
    MODIFICATION = 9
    TOUR = 10
    TCHAT = 11


class Serialisable(ABC):
    @abstractmethod
    def serialiser(self):
        pass

    @abstractmethod
    def deserialiser(x) -> "Serialisable":
        pass


class Paquet(Serialisable):
    def __init__(self, x):
        if not isinstance(x, list):
            raise ValueError("paquet mal formé")
        self.x = x

    def __str__(self):
        return str(self.x)

    def type(self) -> int:
        return self.x[0]

    def serialiser(self):
        return ormsgpack.packb(self.x)

    def deserialiser(x) -> "Paquet":
        return Paquet(ormsgpack.unpackb(x))
