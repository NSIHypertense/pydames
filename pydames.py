import argparse

import gui
import mp.serveur


def type_port(x):
    x = int(x)
    if x < 0 or x > 65535:
        raise argparse.ArgumentTypeError("Le port doit être entre 0 et 65535")
    return x


parseur = argparse.ArgumentParser(prog="pydames", description="Jeu de dâmes")

parseur.add_argument(
    "-s", "--serveur", action="store_true", default=False, help="Héberger un serveur"
)
parseur.add_argument(
    "-p", "--port", type=type_port, default=2332, help="Port du serveur"
)

args = parseur.parse_args()

if args.serveur:
    print("Lancement du serveur...")
    mp.serveur.servir("0.0.0.0", args.port)

    quit()

gui.init()
ecran = gui.Ecran(800, 800)

while ecran.poll():
    ecran.rendre()

gui.fini()
