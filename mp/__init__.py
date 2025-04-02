# Module du multijoueur
from enum import Enum
from abc import ABC, abstractmethod

import ormsgpack


class PaquetClientType(Enum):
    HANDSHAKE = 1
    DEPLACER = 2


class PaquetServeurType(Enum):
    HANDSHAKE = 1
    ERREUR = 2
    DAMIER = 3
    DEPLACEMENTS = 4
    TOUR = 5
    CONCLUSION = 6


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

    def type(self) -> int:
        return self.x[0]

    def serialiser(self):
        return ormsgpack.packb(self.x)

    def deserialiser(x) -> "Paquet":
        return Paquet(ormsgpack.unpackb(x))
