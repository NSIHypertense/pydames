# Module du multijoueur
from enum import Enum
from abc import ABC, abstractmethod

import ormsgpack


class PaquetClientType(Enum):
    HANDSHAKE = 1
    PRET = 2
    DEPLACER = 3
    ANNULER = 4


class PaquetServeurType(Enum):
    HANDSHAKE = 1
    ERREUR = 2
    ATTENTE = 3
    LANCEMENT = 4
    CONCLUSION = 5
    COULEUR = 6
    DEPLACEMENTS = 7
    MODIFICATION = 8
    TOUR = 9


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
