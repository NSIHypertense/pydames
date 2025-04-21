# utilités

import math
from pathlib import Path
import re
import tomllib

conf_defaut = """# configuration du serveur pydames
auto_redemarrage = true   # redémarre le serveur automatiquement lors d'une erreur irrécupérable

[socket]
adresse = "0.0.0.0"       # affecter à "127.0.0.1" pour servir seulement sur la machine locale
port = 2332

[mysql]
hote = "localhost"        # adresse IP ou nom de domaine du serveur MySQL
utilisateur = "pydames"
mdp = "pydames"           # mot de passe
base = "pydames"          # nom de la base de données à utiliser
"""


# source : https://gist.github.com/mathebox/e0805f72e7db3269ec22
class Couleur:
    @staticmethod
    def rgb_to_hsv(r, g, b):
        r = float(r)
        g = float(g)
        b = float(b)
        high = max(r, g, b)
        low = min(r, g, b)
        h, s, v = high, high, high

        d = high - low
        s = 0 if high == 0 else d / high

        if high == low:
            h = 0.0
        else:
            h = {
                r: (g - b) / d + (6 if g < b else 0),
                g: (b - r) / d + 2,
                b: (r - g) / d + 4,
            }[high]
            h /= 6

        return h, s, v

    @staticmethod
    def hsv_to_rgb(h, s, v):
        i = math.floor(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)

        r, g, b = [
            (v, t, p),
            (q, v, p),
            (p, v, t),
            (p, q, v),
            (t, p, v),
            (v, p, q),
        ][int(i % 6)]

        return r, g, b


class ConfigurationServeur:
    def __init__(self, conf: dict):
        assert isinstance(conf, dict)
        assert "auto_redemarrage" in conf

        assert "socket" in conf
        assert "mysql" in conf

        auto_redemarrage = conf["auto_redemarrage"]
        assert isinstance(auto_redemarrage, bool)

        socket = conf["socket"]
        assert isinstance(socket, dict)
        assert "adresse" in socket and isinstance(socket["adresse"], str)
        assert "port" in socket and isinstance(socket["port"], int)

        mysql = conf["mysql"]
        assert isinstance(mysql, dict)
        assert "hote" in mysql and isinstance(mysql["hote"], str)
        assert "utilisateur" in mysql and isinstance(mysql["utilisateur"], str)
        assert "mdp" in mysql and isinstance(mysql["mdp"], str)
        assert "base" in mysql and isinstance(mysql["base"], str)

        self.__auto_redemarrage = auto_redemarrage

        self.__socket = socket
        self.__mysql = mysql

    @property
    def auto_redemarrage(self) -> bool:
        return self.__auto_redemarrage

    @property
    def socket(self) -> dict:
        return self.__socket

    @property
    def mysql(self) -> dict:
        return self.__mysql


_root_pydames = Path(__file__).resolve().parent


def resource_chemin(emplacement: str | Path):
    return _root_pydames / emplacement


def resource(emplacement: str | Path, octets: bool = False):
    return open(
        resource_chemin(emplacement), mode="rb" if octets else "r", encoding="utf-8"
    )


_include_re = re.compile(r'^\s*#\s*include\s+"(.*)"\s*$', re.MULTILINE)


def traiter_glsl(emplacement: Path) -> str:
    assert emplacement.is_file()

    dossier = emplacement.parent

    with open(emplacement, "r") as f:
        source = f.read()

    while resultat := _include_re.search(source):
        include = dossier / resultat.group(1)
        assert include.is_file()

        with open(include, "r") as f:
            source = source[: resultat.start()] + f.read() + source[resultat.end() :]

    def insert_line_numbers(txt):
        return "\n".join(
            [f"{n + 1:03d} {line}" for n, line in enumerate(txt.split("\n"))]
        )

    return source


_fichier_conf = _root_pydames / "serveur.toml"
configuration = None

if _fichier_conf.exists():
    with open(_fichier_conf, "rb") as f:
        configuration = ConfigurationServeur(tomllib.load(f))
else:
    with open(_fichier_conf, "w", encoding="utf-8") as f:
        f.write(conf_defaut)
        print(
            f"Configuration par défaut écrite dans '{_fichier_conf}'. Veuillez la mettre à jour."
        )
