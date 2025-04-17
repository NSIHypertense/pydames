import cmd
import datetime
import select
import socketserver
import sys
import threading
import traceback

from ormsgpack import MsgpackDecodeError
import mysql.connector

from . import Paquet, PaquetClientType, PaquetServeurType
from logic.damier import DAMIER_LARGEUR, DAMIER_LONGUEUR, Pion, Damier
from util import configuration
import bdd

_serv = None
_thread = None

_base = None
_clients = {}

_jeu = None


class Statistiques:
    def __init__(self, score: int, dames: int, pions_restants: int):
        self.__score, self.__dames, self.__pions_restants = score, dames, pions_restants

    @property
    def score(self) -> int:
        return self.__score

    @property
    def dames(self) -> int:
        return self.__dames

    @property
    def pions_restants(self) -> int:
        return self.__pions_restants

    def sauter(self, sauts: int):
        self.__score += sauts
        self.__pions_restants -= sauts

    def dame(self):
        self.__score += 2
        self.__dames += 1


class Jeu:
    def __init__(self):
        self.id = _base.ajouter_jeu() if _base else None
        self.partie = Partie(self.id)
        self.__sock_noir, self.__sock_blanc, self.__joueurs = None, None, {}

    @property
    def sock_noir(self):
        return self.__sock_noir

    @property
    def sock_blanc(self):
        return self.__sock_blanc

    @property
    def joueurs(self) -> dict[str, int]:
        return self.__joueurs.copy()

    def affecter_sockets(self):
        tab_clients = list(_clients)
        assert len(tab_clients) == 2

        self.__sock_noir = tab_clients[0]
        self.__sock_blanc = tab_clients[1]

    def couleur(self, sock) -> Pion | None:
        if sock == self.__sock_noir:
            return Pion.NOIR
        elif sock == self.__sock_blanc:
            return Pion.BLANC
        else:
            return None

    def statistiques(self, sock) -> Statistiques | None:
        assert self.partie

        match self.couleur(sock):
            case Pion.NOIR:
                return self.partie.stat_noir
            case Pion.BLANC:
                return self.partie.stat_blanc
            case _:
                return None

    def creer_joueur(self, pseudo: str):
        if _base:
            self.__joueurs[pseudo] = _base.ajouter_joueur(pseudo)

    def obtenir_joueur(self, pseudo: str) -> int | None:
        return self.__joueurs.get(pseudo)


class Partie:
    def __init__(self, id_jeu: int):
        self.__id_jeu = id_jeu
        self.damier = Damier(DAMIER_LONGUEUR, DAMIER_LARGEUR)
        self.__id_noir = self.__id_blanc = self.__debut = self.__fin = (
            self.stat_noir
        ) = self.stat_blanc = None

    @property
    def debut(self) -> datetime.datetime:
        return self.__debut

    @property
    def fin(self) -> datetime.datetime:
        return self.__fin

    def demarrer(self, noir: str, blanc: str):
        self.damier.installer()

        if _base:
            self.__id_noir, self.__id_blanc = (
                _base.ajouter_joueur(noir),
                _base.ajouter_joueur(blanc),
            )

        self.stat_noir = Statistiques(
            0,
            0,
            sum(
                1
                for ligne in self.damier.matrice
                for p in ligne
                if p == Pion.NOIR or p == Pion.DAME_NOIR
            ),
        )
        self.stat_blanc = Statistiques(
            0,
            0,
            sum(
                1
                for ligne in self.damier.matrice
                for p in ligne
                if p == Pion.BLANC or p == Pion.DAME_BLANC
            ),
        )

        self.__debut = datetime.datetime.now()
        self.__fin = None

    def arreter(self):
        self.__fin = datetime.datetime.now()

        if _base:
            id_stat_noir = _base.ajouter_statistiques(
                self.stat_noir.score,
                self.stat_noir.dames,
                self.stat_noir.pions_restants,
            )
            id_stat_blanc = _base.ajouter_statistiques(
                self.stat_blanc.score,
                self.stat_blanc.dames,
                self.stat_blanc.pions_restants,
            )

            id_equipe_noir = _base.ajouter_equipe(self.__id_noir, id_stat_noir)
            id_equipe_blanc = _base.ajouter_equipe(self.__id_blanc, id_stat_blanc)

            _base.ajouter_partie(
                self.__id_jeu,
                id_equipe_noir,
                id_equipe_blanc,
                str(self.__debut),
                str(self.__fin),
            )


class DonneesClient:
    def __init__(self):
        self.etat_pret, self.pseudo, self.file_paquets = False, None, []


class Gestionnaire(socketserver.BaseRequestHandler):
    def setup(self):
        global _clients

        _clients[self.request] = DonneesClient()

    def erreur(self, *args, **kwargs):
        global _clients

        print(f"({self.client_address[0]}) erreur:", *args, file=sys.stderr, **kwargs)
        self.envoyer(_paquet_erreur(" ".join(map(str, args))))
        del _clients[self.request]

    def envoyer(self, paquet: Paquet):
        _envoyer(self.request, paquet)

    def mettre_pret(self):
        global _clients

        _clients[self.request].etat_pret = True

    def handle(self):
        global _clients

        n_client = len(_clients) - 1

        if n_client >= 2:
            self.erreur("trop de clients !")
            return

        self.envoyer(_paquet_handshake())

        while True:
            r, w, _ = select.select([self.request], [self.request], [])

            if w:  # ecrire
                file = _clients[self.request].file_paquets
                if file:
                    octets = file.pop(0)
                    self.request.sendall(octets)
                    continue

            if not r:  # lire
                continue

            parties = []
            octets = self.request.recv(4)

            if not octets:
                self.erreur("la connexion a été fermée")
                break

            if len(octets) < 4:
                self.erreur("paquet mal formé, header taille invalide")
                break

            taille_paquet = int.from_bytes(octets[:4], byteorder="little", signed=False)

            while True:
                total = sum([len(x) for x in parties])
                if total >= taille_paquet:
                    break

                parties.append(self.request.recv(taille_paquet - total))

            octets = b"".join(parties)

            try:
                paquet = Paquet.deserialiser(octets)
            except MsgpackDecodeError:
                self.erreur("paquet mal formé, erreur msgpack")
                break
            except ValueError as e:
                self.erreur(e)
                break

            # print(f"({self.client_address[0]}) reçu paquet: {paquet.x}")

            try:
                match paquet.type():
                    case PaquetClientType.HANDSHAKE.value:
                        if _clients.get(self.request).pseudo:
                            self.erreur("La connexion a déjà été établie !")
                        else:
                            pseudo = paquet.x[1]

                            if not isinstance(pseudo, str) or not (
                                3 <= len(pseudo) <= 24
                            ):
                                self.erreur("pseudonyme invalide")
                                break

                            if pseudo in [d.pseudo for d in _clients.values()]:
                                self.erreur("pseudonyme déjà pris")
                                break

                            _clients[self.request].pseudo = pseudo
                            print(
                                f"({self.client_address[0]}) connecté en tant que '{pseudo}'"
                            )

                            self.envoyer(_paquet_couleur(_couleur_client(n_client)))
                            if n_client == 0:
                                self.envoyer(_paquet_tour())
                    case PaquetClientType.PRET.value:
                        if _jeu.partie.debut and not _jeu.partie.fin:
                            self.erreur("La partie est déjà commencée !")
                        else:
                            self.mettre_pret()
                            print(f"({self.client_address[0]}) {pseudo} : prêt")

                            if len(_clients) == 2:
                                tous_prets = all(d.etat_pret for d in _clients.values())

                                if tous_prets:
                                    _jeu.affecter_sockets()
                                    noir, blanc = _jeu.sock_noir, _jeu.sock_blanc

                                    _jeu.partie.demarrer(
                                        _clients[noir].pseudo, _clients[blanc].pseudo
                                    )
                                    _diffuser(_paquet_lancement())
                                    print("Partie lancée")
                    case PaquetClientType.DEPLACER.value:
                        if _jeu.partie.fin:
                            self.erreur("La partie est déjà finie !")
                        else:
                            source, cible = tuple(paquet.x[1]), tuple(paquet.x[2])

                            if cible in _jeu.partie.damier.trouver_cases_possibles(
                                *source
                            ):
                                sauts = _jeu.partie.damier.deplacer_pion(source, cible)
                                _diffuser(_paquet_deplacements([source, cible]))
                                _jeu.statistiques(self.request).sauter(len(sauts))

                                if gagnant := _jeu.partie.damier.gagnant():
                                    _jeu.partie.arreter()
                                    _diffuser(_paquet_conclusion(gagnant))
                                    print(f"Partie terminée : {gagnant}")
                                elif _jeu.partie.damier.est_bloque():
                                    _jeu.partie.arreter()
                                    _diffuser(_paquet_conclusion(None))
                                    print("Partie terminée : aucun gagnant")
                                else:
                                    # redonner au joueur encore un tour s'il peut sauter par dessus des pions adverses
                                    encore = False

                                    if sauts:
                                        for (
                                            c
                                        ) in _jeu.partie.damier.trouver_cases_possibles(
                                            *cible
                                        ):
                                            if encore := bool(
                                                _jeu.partie.damier.deplacer_pion(
                                                    cible, c, False
                                                )
                                            ):
                                                break

                                    adversaire = next(
                                        (
                                            c
                                            for c in _clients.keys()
                                            if c != self.request
                                        ),
                                        None,
                                    )

                                    if encore:
                                        self.envoyer(_paquet_tour(cible))
                                    elif not adversaire:
                                        self.envoyer(_paquet_tour())
                                    else:
                                        _envoyer(adversaire, _paquet_tour())
                            else:
                                self.erreur(
                                    f"déplacement illégal : {source} -> {cible}"
                                )
                    case PaquetClientType.ANNULER.value:
                        adversaire = next(
                            (c for c in _clients.keys() if c != self.request),
                            None,
                        )

                        if adversaire:
                            _envoyer(adversaire, _paquet_tour())
                        else:
                            self.erreur("aucun adversaire trouvé !")
                    case _:
                        self.erreur(f"paquet de type inconnu ({paquet.type()})")
                        break
            except (IndexError, KeyError):
                self.erreur(f"paquet mal formé ({paquet})")
                print(traceback.format_exc())
                break

    def finish(self):
        global _clients

        if _clients:
            _clients.pop(self.request, None)
            for donnees in _clients.values():
                donnees.etat_pret = False
            _diffuser(_paquet_attente())


def _construire_paquet(paquet: Paquet) -> bytes:
    octets = paquet.serialiser()
    octets = len(octets).to_bytes(4, byteorder="little", signed=False) + octets
    return octets


def _paquet_handshake() -> Paquet:
    return Paquet([PaquetServeurType.HANDSHAKE])


def _paquet_erreur(message: str) -> Paquet:
    return Paquet([PaquetServeurType.ERREUR])


def _paquet_attente() -> Paquet:
    return Paquet([PaquetServeurType.ATTENTE])


def _paquet_lancement() -> Paquet:
    return Paquet([PaquetServeurType.LANCEMENT, _jeu.partie.damier.matrice])


def _paquet_conclusion(gagnant: Pion | None) -> Paquet:
    return Paquet([PaquetServeurType.CONCLUSION, gagnant])


def _paquet_couleur(couleur: Pion) -> Paquet:
    return Paquet([PaquetServeurType.COULEUR, couleur])


def _paquet_deplacements(deplacements: list[tuple[int, int]]) -> Paquet:
    return Paquet([PaquetServeurType.DEPLACEMENTS, deplacements])


def _paquet_modification(position: tuple[int, int], nouveau: Pion) -> Paquet:
    return Paquet([PaquetServeurType.MODIFICATION, position, nouveau])


def _paquet_tour(position: tuple[int, int] | None = None) -> Paquet:
    return Paquet([PaquetServeurType.TOUR, position])


def _envoyer(client, paquet: Paquet):
    octets = _construire_paquet(paquet)
    _clients[client].file_paquets.append(octets)


def _diffuser(paquet: Paquet):
    octets = _construire_paquet(paquet)
    for donnees in _clients.values():
        donnees.file_paquets.append(octets)


def _couleur_client(n: int) -> Pion:
    return Pion(1 + n % 2)


def demarrer(destination: str, port: int):
    global _base
    global _serv
    global _thread

    global _jeu

    try:
        _base = bdd.Base(
            configuration.mysql["hote"],
            configuration.mysql["utilisateur"],
            configuration.mysql["mdp"],
            configuration.mysql["base"],
        )
    except mysql.connector.Error as e:
        print(e)
        print("Le serveur sera démarré sans base de données.")

    _jeu = Jeu()

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    _serv = socketserver.ThreadingTCPServer((destination, port), Gestionnaire)

    _thread = threading.Thread(target=_serv.serve_forever)
    _thread.start()


def arreter():
    global _base
    global _serv
    global _thread

    if _serv:
        print("arrêt du serveur...")
        try:
            _serv.shutdown()
        except OSError:
            pass
        _serv.server_close()
        _serv = None

    if _thread:
        _thread.join()
        _thread = None

    if _base:
        _base.arreter()
        _base = None


class Console(cmd.Cmd):
    intro = "Console du serveur pydames\nSaisissez 'help' ou '?' pour afficher les commandes."
    prompt = "pydames> "

    def __init__(self):
        super().__init__()
        self.alias = {"q": self.do_arreter}

    def precmd(self, line):
        cmd, _, line = self.parseline(line)
        if cmd in self.alias:
            line = f"{self.alias[cmd].__name__[3:]}{line[len(cmd) :]}"
        return line

    def do_help(self, arg):
        "Affiche les commandes disponibles avec 'help' ou affiche plus de détails sur une commande avec 'help commande'."

        if arg in self.alias:
            arg = self.alias[arg].__name__[3:]
        super().do_help(arg)

        if not arg:
            for k, v in self.alias.items():
                print(k, v.__name__[3:])

    def do_arreter(self, arg):
        "Arrête le serveur pydames."
        arreter()
        return True

    def do_finir(self, arg):
        "Finit la partie."
        if not _jeu.partie or not _jeu.partie.debut:
            print("Il n'y a encore de partie démarrée !")
        _jeu.partie.arreter()
        _diffuser(_paquet_conclusion(None))
        print("partie arrêtée.")
