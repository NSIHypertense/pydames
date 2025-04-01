# Module de l'interface graphique
from . import ecran
from .ecran import Ecran


def init():
    ecran.init()


def fini():
    ecran.fini()
