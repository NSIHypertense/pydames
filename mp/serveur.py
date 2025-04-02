import socketserver
import sys

from ormsgpack import MsgpackDecodeError

from logic.damier import DAMIER_LARGEUR, DAMIER_LONGUEUR, CouleurPion, Damier

from . import Paquet, PaquetClientType, PaquetServeurType

clients = []

damier = Damier(DAMIER_LONGUEUR, DAMIER_LARGEUR)
damier.installer()

fini = False


def construire_paquet(paquet: Paquet) -> bytes:
    octets = paquet.serialiser()
    octets = len(octets).to_bytes(4, byteorder="little", signed=False) + octets
    return octets


def paquet_handshake() -> Paquet:
    return Paquet([PaquetServeurType.HANDSHAKE])


def paquet_erreur(message: str) -> Paquet:
    return Paquet([PaquetServeurType.ERREUR])


def paquet_damier(couleur: CouleurPion) -> Paquet:
    return Paquet([PaquetServeurType.DAMIER, couleur, damier.matrice])


def paquet_deplacements(deplacements: list[tuple[int, int]]) -> Paquet:
    return Paquet([PaquetServeurType.DEPLACEMENTS, deplacements])


def paquet_tour() -> Paquet:
    return Paquet([PaquetServeurType.TOUR])


def paquet_conclusion(gagnant: CouleurPion | None) -> Paquet:
    return Paquet([PaquetServeurType.CONCLUSION, gagnant])


class Gestionnaire(socketserver.BaseRequestHandler):
    def setup(self):
        global clients

        clients.append(self.request)

    def erreur(self, *args, **kwargs):
        global clients

        print(f"({self.client_address[0]}) erreur:", *args, file=sys.stderr, **kwargs)
        self.envoyer(paquet_erreur(" ".join(map(str, args))))
        clients.remove(self.request)

    def envoyer(self, paquet: Paquet):
        octets = construire_paquet(paquet)
        self.request.sendall(octets)

    def diffuser(self, paquet: Paquet):
        global clients

        octets = construire_paquet(paquet)
        for client in clients:
            client.sendall(octets)

    def handle(self):
        global clients
        global damier
        global fini

        n_client = clients.index(self.request)

        if len(clients) > 2:
            self.erreur("trop de clients !")
            return

        self.envoyer(paquet_handshake())

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

            try:
                match paquet.type():
                    case PaquetClientType.HANDSHAKE.value:
                        self.envoyer(paquet_damier(CouleurPion(1 + n_client % 2)))
                        if n_client == 0:
                            self.envoyer(paquet_tour())
                    case PaquetClientType.DEPLACER.value:
                        if fini:
                            self.erreur("la partie est finie !")

                        source, cible = tuple(paquet.x[1]), tuple(paquet.x[2])

                        if cible in damier.trouver_cases_possibles(*source):
                            damier.deplacer_pion(source, cible)
                            self.diffuser(paquet_deplacements([source, cible]))

                            if gagnant := damier.gagnant():
                                fini = True
                                self.diffuser(paquet_conclusion(gagnant))
                            elif damier.est_bloque():
                                fini = True
                                self.diffuser(paquet_conclusion(None))
                        else:
                            self.erreur(f"déplacement illégal : {source} -> {cible}")

                        if not fini:
                            n_autre = (n_client + 1) % len(clients)
                            clients[n_autre].sendall(construire_paquet(paquet_tour()))
                    case _:
                        self.erreur("paquet de type inconnu")
                        return
            except (IndexError, KeyError):
                self.erreur("paquet mal formé")
                return


def servir(destination: str, port: int):
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer((destination, port), Gestionnaire) as server:
        server.serve_forever()
