import socket
import sys
import threading

from ormsgpack import MsgpackDecodeError

from logic.damier import CouleurPion, Damier

from . import Paquet, PaquetClientType, PaquetServeurType

sock = None
connexion_succes = False
connexion_erreur = False
thread = None

couleur = None
damier = None
tour = False
deplacements = []
sauts = []


def connecter(destination: str, port: int) -> socket.socket:
    print("création du socket")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("connexion tcp au serveur...")
    s.connect((destination, port))
    print("connecté tcp")
    return s


def paquet_handshake() -> Paquet:
    return Paquet([PaquetClientType.HANDSHAKE])


def paquet_deplacer(source: tuple[int, int], cible: tuple[int, int]) -> Paquet:
    return Paquet([PaquetClientType.DEPLACER, source, cible])


def erreur(*args, **kwargs):
    print("erreur multijoueur :", *args, file=sys.stderr, **kwargs)


def envoyer(paquet: Paquet):
    octets = paquet.serialiser()
    octets = len(octets).to_bytes(4, byteorder="little", signed=False) + octets
    sock.sendall(octets)


def thread_client():
    global connexion_succes

    global couleur
    global damier
    global tour
    global deplacements
    global sauts

    def arreter():
        global sock
        global connexion_erreur
        global connexion_succes

        connexion_erreur = True
        connexion_succes = False
        sock.close()
        sock = None

    while sock:
        parties = []
        octets = sock.recv(4)

        if len(octets) < 4:
            erreur("paquet mal formé, header taille invalide")
            arreter()
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
            arreter()
            return
        except ValueError as e:
            erreur(e)
            arreter()
            return

        print(f"recu paquet: {paquet.x}")

        try:
            match paquet.type():
                case PaquetServeurType.HANDSHAKE.value:
                    envoyer(paquet_handshake())
                    print("Connexion établie")
                    connexion_succes = True
                case PaquetServeurType.ERREUR.value:
                    erreur(paquet.x[1])
                    arreter()
                    return
                case PaquetServeurType.DAMIER.value:
                    couleur = CouleurPion(paquet.x[1])
                    damier = Damier.from_matrice(paquet.x[2])
                case PaquetServeurType.DEPLACEMENTS.value:
                    tour = False
                    for i in range(0, len(paquet.x[1]), 2):
                        source, cible = tuple(paquet.x[1][i]), tuple(paquet.x[1][i + 1])
                        deplacements.extend([source, cible])
                        sauts.append(damier.deplacer_pion(source, cible))
                case PaquetServeurType.TOUR.value:
                    tour = True
                case PaquetServeurType.CONCLUSION.value:
                    print("La partie est finie.")
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
                case _:
                    erreur("paquet de type inconnu")
                    arreter()
                    return
        except (IndexError, KeyError):
            erreur("paquet mal formé")
            return


def demarrer_client():
    global connexion_erreur
    global connexion_succes
    global thread

    if not sock:
        raise RuntimeError("aucun socket connecté")

    connexion_erreur = False
    connexion_succes = False

    thread = threading.Thread(target=thread_client)
    thread.start()
