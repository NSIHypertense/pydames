import random
import socket
import sys
import threading

from ormsgpack import MsgpackDecodeError

from logic.damier import CouleurPion, Damier

from . import Paquet, PaquetClientType, PaquetServeurType

# Joueur
pseudo = f"Joueur{random.randint(0, 999):03}"

# Connexion
connexion_succes = False
connexion_erreur = False
serveur = None
sock = None
thread = None

# Partie
attente = True
pret = False
couleur = None
damier = None
tour = False
deplacements = []
sauts = []


def paquet_handshake(pseudo: str) -> Paquet:
    return Paquet([PaquetClientType.HANDSHAKE, pseudo])


def paquet_pret() -> Paquet:
    return Paquet([PaquetClientType.PRET])


def paquet_deplacer(source: tuple[int, int], cible: tuple[int, int]) -> Paquet:
    return Paquet([PaquetClientType.DEPLACER, source, cible])


def erreur(*args, **kwargs):
    print("erreur multijoueur :", *args, file=sys.stderr, **kwargs)
    arreter()


def envoyer(paquet: Paquet):
    octets = paquet.serialiser()
    octets = len(octets).to_bytes(4, byteorder="little", signed=False) + octets
    sock.sendall(octets)


def thread_client():
    global connexion_succes

    global attente
    global pret
    global couleur
    global damier
    global tour
    global deplacements
    global sauts

    while sock:
        parties = []
        octets = sock.recv(4)

        if not octets:
            erreur("la connexion a été fermée")
            return

        if len(octets) < 4:
            erreur("paquet mal formé, header taille invalide")
            return

        taille_paquet = int.from_bytes(octets[:4], byteorder="little", signed=False)

        while True:
            total = sum([len(x) for x in parties])
            if total >= taille_paquet:
                break

            parties.append(sock.recv(taille_paquet - total))

        octets = b"".join(parties)

        try:
            paquet = Paquet.deserialiser(octets)
        except MsgpackDecodeError:
            erreur("paquet mal formé, erreur msgpack")
            return
        except ValueError as e:
            erreur(e)
            return

        # print(f"reçu paquet: {paquet.x}")

        try:
            match paquet.type():
                case PaquetServeurType.HANDSHAKE.value:
                    envoyer(paquet_handshake(pseudo))
                    print("Connexion au serveur pydames établie")
                    connexion_succes = True
                case PaquetServeurType.ERREUR.value:
                    erreur(paquet.x[1])
                    return
                case PaquetServeurType.ATTENTE.value:
                    print("L'adversaire s'est déconnecté du serveur.")
                    pret = False
                    attente = True
                case PaquetServeurType.LANCEMENT.value:
                    attente = False
                    damier = Damier.from_matrice(paquet.x[1])
                case PaquetServeurType.CONCLUSION.value:
                    print("La partie est finie.")
                    attente = True
                    gagnant = paquet.x[1]

                    if gagnant:
                        print(
                            "Les",
                            "noirs" if gagnant == CouleurPion.NOIR.value else "blancs",
                            "ont remporté la victoire.",
                        )
                    else:
                        print("Il n'y a aucun gagnant ni perdant.")

                    arreter()
                    return
                case PaquetServeurType.COULEUR.value:
                    couleur = CouleurPion(paquet.x[1])
                case PaquetServeurType.DEPLACEMENTS.value:
                    tour = False
                    for i in range(0, len(paquet.x[1]), 2):
                        source, cible = tuple(paquet.x[1][i]), tuple(paquet.x[1][i + 1])
                        deplacements.extend([source, cible])
                        saut = damier.deplacer_pion(source, cible)
                        if saut:
                            sauts.append(saut)
                case PaquetServeurType.TOUR.value:
                    tour = True
                case _:
                    erreur("paquet de type inconnu")
                    return
        except (IndexError, KeyError):
            erreur("paquet mal formé")
            return


def demarrer(destination: str, port: int):
    global connexion_erreur
    global connexion_succes
    global serveur
    global sock
    global thread

    serveur = (destination, port)

    print("création du socket")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("connexion TCP au serveur...")
    sock.connect((destination, port))
    print("connexion TCP établie")

    connexion_erreur = False
    connexion_succes = False

    thread = threading.Thread(target=thread_client)
    thread.start()


def arreter():
    global attente
    global pret

    global connexion_erreur
    global connexion_succes
    global sock
    global thread

    pret = False
    attente = True

    connexion_erreur = False
    connexion_succes = False

    if sock:
        print("arrêt du client...")
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        sock = None

    if thread:
        if thread is not threading.current_thread():
            thread.join()
        thread = None
