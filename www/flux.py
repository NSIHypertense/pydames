import threading
import traceback
import socket
import websockets
from websockets.sync.server import serve

_serveur = None
_thread = None
_port_pydames = None


class Passerelle:
    def __init__(self, destination, port, ws):
        self.ws = ws
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((destination, port))

    def main(self, flux_id):
        message = b"flux" + flux_id.encode("utf-8")
        message = len(message).to_bytes(4, byteorder="little", signed=False) + message
        self.sock.sendall(message)

        while self.running:
            data = self.sock.recv(4096)
            if not data:
                break
            self.ws.send(data)

    def close(self):
        self.sock.close()


def _gestionnaire(ws):
    global _port_pydames

    passerelle = None

    try:
        # Recevoir le message d'initialisation
        message = ws.recv()

        # Démarrer le forwarder TCP
        passerelle = Passerelle("127.0.0.1", _port_pydames, ws)
        passerelle.main(message)
    except (ConnectionError, websockets.exceptions.ConnectionClosed):
        pass
    except Exception:
        print("[Flux] erreur :")
        print(traceback.format_exc())

    if passerelle:
        passerelle.close()


def demarrer(adresse: str, port: int, port_pydames: int):
    global _serveur
    global _thread
    global _port_pydames

    _port_pydames = port_pydames

    def servir():
        _serveur = serve(_gestionnaire, adresse, port)
        _serveur.serve_forever()

    _thread = threading.Thread(target=servir, daemon=True)
    _thread.start()


def arreter():
    global _serveur
    global _thread

    if _serveur:
        _serveur.shutdown()
        _serveur = None

    if _thread:
        _thread.join(timeout=1)
        _thread = None
