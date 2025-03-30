import argparse

from logic.pion import Pion
import gui

parser = argparse.ArgumentParser(
    prog="pydames",
    description="Jeu de dâmes")

args = parser.parse_args()

gui.init()
ecran = gui.Ecran(800, 800)

while ecran.poll():
    ecran.rendre()

gui.fini()
