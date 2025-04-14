# Module de l'interface graphique
from . import ecran
from .ecran import Ecran

__all__ = ["Ecran"]


def init():
    ecran.init()


def fini():
    ecran.fini()
