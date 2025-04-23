import sys
import argparse

import mp.client
import mp.serveur
import util


def type_port(x):
    x = int(x)
    if x < 0 or x > 65535:
        raise argparse.ArgumentTypeError("Le port doit être entre 0 et 65535")
    return x


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(prog="pydames", description="Jeu de dâmes")

    parseur.add_argument(
        "-s",
        "--serveur",
        action="store_true",
        default=False,
        help="Héberger un serveur",
    )

    parseur.add_argument(
        "-p",
        "--portable",
        action="store_true",
        default=False,
        help="Ne pas sauvegarder les réglages du jeu",
    )

    parseur.add_argument(
        "-P",
        "--pseudo-aleatoire",
        action="store_true",
        default=False,
        help="Utilise toujours un pseudonyme aléatoire",
    )

    args = parseur.parse_args()

    if args.serveur:
        if not util.configuration:
            print("Erreur : la configuration du serveur n'a pas été trouvée !")
            quit()

        print("Lancement du serveur...")
        mp.serveur.demarrer(
            util.configuration.socket["adresse"], util.configuration.socket["port"]
        )
        mp.serveur.Console().cmdloop()
    else:
        import gui

        if args.pseudo_aleatoire:
            mp.client.reglages.pseudo_force = True
            mp.client.reglages.pseudo = util.Reglages.pseudo_aleatoire()

        gui.init()
        ecran = gui.Ecran(800, 800)

        while ecran.poll():
            ecran.rendre()

        ecran.fini()
        mp.client.arreter()
        gui.fini()

        if not args.portable:
            util.sauvegarder_reglages(mp.client.reglages)
