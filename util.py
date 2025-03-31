# utilités
import pathlib

class Couleurs:
    noir = (0,0,0)
    blanc = (255,255,255)
    vert = (0,255,0)

script_directory = pathlib.Path(__file__).resolve().parent

def resource(emplacement: str | pathlib.Path, octets: bool=False):
    return open(script_directory / emplacement, mode='rb' if octets else 'r')

