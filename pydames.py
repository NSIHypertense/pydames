import argparse
import atexit
import traceback

import mp.client
import mp.serveur
import util
from util import configuration
from www import Php


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

    parseur.add_argument(
        "--php",
        action="store_true",
        default=False,
        help="Héberge seulement le serveur PHP",
    )

    args = parseur.parse_args()

    if args.serveur:
        if not configuration:
            print("Erreur : la configuration du serveur n'a pas été trouvée !")
            quit()

        processus_php = None

        if configuration.php["actif"] or args.php:
            print("Lancement du serveur PHP...")

            if fichier_env := configuration.php["env"]:
                with open(fichier_env, "w") as f:
                    Php.generer_env(f, configuration)

            try:
                serveur = configuration.php["serveur"]
                if serveur:
                    serveur = util.resource_chemin(serveur)
                php = Php.trouver(serveur)

                if not php and serveur and configuration.php["telecharger"]:
                    serveur.mkdir(exist_ok=True)
                    php = Php.telecharger(serveur)
                if not php:
                    raise RuntimeError("aucun exécutable PHP n'a été trouvé")

                site = util.resource_chemin(configuration.php["site"])
                processus_php = Php.lancer(
                    php,
                    util.resource_chemin(configuration.php["config"]),
                    site,
                    configuration.php["adresse"],
                    configuration.php["port"],
                )
                assert processus_php

                atexit.register(lambda: Php.arreter(processus_php))
            except Exception:
                print("Le serveur PHP n'a pas pu être démarré.")
                print(traceback.format_exc())

        if not args.php:
            print("Lancement du serveur pydames...")
            mp.serveur.demarrer(
                configuration.socket["adresse"], configuration.socket["port"]
            )
            mp.serveur.Console().cmdloop()

        if processus_php:
            Php.attendre(processus_php)
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
