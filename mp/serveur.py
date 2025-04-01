from enum import Enum
import socketserver
import sys

from ormsgpack import MsgpackDecodeError

from . import Paquet
from .client import PaquetClientType


class PaquetServeurType(Enum):
    HANDSHAKE = 1


class Gestionnaire(socketserver.BaseRequestHandler):
    def erreur(self, *args, **kwargs):
        print(f"({self.client_address[0]}) erreur:", *args, file=sys.stderr, **kwargs)

    def envoyer(self, paquet: Paquet):
        octets = paquet.serialiser()
        octets = len(octets).to_bytes(4, byteorder="little", signed=False) + octets
        self.request.sendall(octets)

    def handle(self):
        while True:
            parties = []
            octets = self.request.recv(4)

            if len(octets) < 4:
                self.erreur("paquet mal formé, header taille invalide")
                return

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
                return
            except ValueError as e:
                self.erreur(e)
                return

            print(f"({self.client_address[0]}) recu paquet: {paquet.x}")

            match paquet.type():
                case PaquetClientType.HANDSHAKE.value:
                    self.envoyer(paquet_handshake())
                case _:
                    self.erreur("paquet de type inconnu")
                    return


def paquet_handshake() -> Paquet:
    return Paquet([PaquetServeurType.HANDSHAKE])


def servir(destination: str, port: int):
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((destination, port), Gestionnaire) as server:
        server.serve_forever()
