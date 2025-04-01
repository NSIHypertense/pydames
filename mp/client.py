from enum import Enum
import socket
import sys
import threading

from ormsgpack import MsgpackDecodeError

from . import Paquet

sock = None
succes = False
thread = None


class PaquetClientType(Enum):
    HANDSHAKE = 1


def connecter(destination: str, port: int) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((destination, port))
    return s


def paquet_handshake() -> Paquet:
    return Paquet([PaquetClientType.HANDSHAKE])


def erreur(*args, **kwargs):
    print("erreur multijoueur :", *args, file=sys.stderr, **kwargs)


def envoyer(paquet: Paquet):
    octets = paquet.serialiser()
    octets = len(octets).to_bytes(4, byteorder="little", signed=False) + octets
    sock.sendall(octets)


def thread_client():
    global succes

    def arreter():
        global sock
        global succes

        succes = False
        sock.close()
        sock = None

    envoyer(paquet_handshake())

    while True:
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

        match paquet.type():
            case PaquetClientType.HANDSHAKE.value:
                print("Connexion établie")
                succes = True
            case _:
                erreur("paquet de type inconnu")
                arreter()
                return


def demarrer_client():
    global succes
    global thread

    if not sock:
        raise RuntimeError("aucun socket connecté")
    succes = False

    thread = threading.Thread(target=thread_client)
    thread.start()
