# Module de la base de données
import mysql.connector

import util


class Base:
    def __init__(
        self, hote: str, port: int, utilisateur: str, mdp: str, base: str, ssl: bool
    ):
        self.__connexion = None

        try:
            print(
                f"Connexion à la base de données en cours... ('{utilisateur}'@'{hote}' : {base})"
            )
            self.__connexion = mysql.connector.connect(
                host=hote,
                port=port,
                user=utilisateur,
                password=mdp,
                database=base,
                ssl_disabled=not ssl,
            )
            self.__curseur = self.__connexion.cursor()

            print("succès connexion BDD. Création des tables...")
            with util.resource("bdd/bdd.sql") as schema:
                resultat = self.__curseur.execute(schema.read(), multi=True)
                self.__connexion.commit()

                while True:  # le script n'est pas évalué sans ce bout de code
                    try:
                        next(resultat).fetchall()
                    except Exception:
                        break

            print("succès BDD.")
        except mysql.connector.Error as e:
            print("erreur BDD !")
            raise e

    def ajouter_jeu(self):
        requete = "INSERT INTO jeux () VALUES ()"
        self.__curseur.execute(requete)
        self.__connexion.commit()
        return self.__curseur.lastrowid

    def ajouter_joueur(self, nom: str):
        requete = "SELECT id FROM joueurs WHERE nom = %s"
        self.__curseur.execute(requete, (nom,))
        resultat = self.__curseur.fetchone()

        if resultat:
            return resultat[0]

        requete = "INSERT INTO joueurs (nom) VALUES (%s)"
        self.__curseur.execute(requete, (nom,))
        self.__connexion.commit()
        return self.__curseur.lastrowid

    def ajouter_statistiques(self, score: int, dames: int, pions_restants: int):
        requete = "INSERT INTO statistiques (score, dames, pions_restants) VALUES (%s, %s, %s)"
        self.__curseur.execute(requete, (score, dames, pions_restants))
        self.__connexion.commit()
        return self.__curseur.lastrowid

    def ajouter_equipe(self, id_joueur: int, id_statistiques: int):
        requete = "INSERT INTO equipes (id_joueur, id_statistiques) VALUES (%s, %s)"
        self.__curseur.execute(requete, (id_joueur, id_statistiques))
        self.__connexion.commit()
        return self.__curseur.lastrowid

    def ajouter_partie(
        self, id_jeu: int, id_noir: int, id_blanc: int, debut: str, fin: str
    ):
        requete = "INSERT INTO parties (id_jeu, id_noir, id_blanc, debut, fin) VALUES (%s, %s, %s, %s, %s)"
        self.__curseur.execute(requete, (id_jeu, id_noir, id_blanc, debut, fin))
        self.__connexion.commit()
        return self.__curseur.lastrowid

    def obtenir_joueurs(self):
        self.__curseur.execute("SELECT * FROM joueurs")
        return self.__curseur.fetchall()

    def obtenir_parties(self):
        self.__curseur.execute("SELECT * FROM parties")
        return self.__curseur.fetchall()

    def arreter(self):
        self.__curseur.close()
        self.__connexion.close()
