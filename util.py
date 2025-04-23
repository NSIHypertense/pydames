# utilités

import colorsys
import math
from pathlib import Path
import random
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


class ConfigurationServeur:
    def __init__(self, conf: dict):
        assert isinstance(conf, dict)

        auto_redemarrage = conf.get("auto_redemarrage")
        assert isinstance(auto_redemarrage, bool)

        socket = conf.get("socket")
        assert isinstance(socket, dict)
        assert isinstance(socket.get("adresse"), str)
        assert isinstance(socket.get("port"), int)

        mysql = conf.get("mysql")
        assert isinstance(mysql, dict)
        assert isinstance(mysql.get("hote"), str)
        assert isinstance(mysql.get("utilisateur"), str)
        assert isinstance(mysql.get("mdp"), str)
        assert isinstance(mysql.get("base"), str)

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


class Reglages:
    def __init__(self, reglages: dict):
        self.pseudo_force = False

        if not reglages:
            self.pseudo: str = Reglages.pseudo_aleatoire()
            self.taille_damier: int = 8
            self.duree_animation: float = 0.3
            self.couleurs = {
                "noir": [0.0, 0.0, 0.0],
                "blanc": [1.0, 1.0, 1.0],
                "dame_noir": [1.0, 0.4, 0.3],
                "dame_blanc": [0.4, 0.6, 1.0],
                "damier_noir": list(colorsys.hsv_to_rgb(0.6, 0.2, 0.05)),
                "damier_blanc": list(colorsys.hsv_to_rgb(0.6, 0.05, 1.0)),
                "bordure": [1.0, 0.0, 1.0],
                "cases_possibles": [0.0, 0.0, 1.0],
                "cases_deplacements": [0.0, 1.0, 0.0],
            }
            return

        assert isinstance(reglages, dict)

        self.pseudo: str = reglages.get("pseudo")
        assert isinstance(self.pseudo, str)

        self.taille_damier: int = reglages.get("taille_damier")
        assert isinstance(self.taille_damier, int)

        self.duree_animation: float = reglages.get("duree_animation")
        assert isinstance(self.duree_animation, (float, int))
        self.duree_animation = float(self.duree_animation)

        self.couleurs: dict = reglages.get("couleurs")
        assert isinstance(self.couleurs, dict)
        assert (
            isinstance(self.couleurs.get("noir"), list)
            and len(self.couleurs["noir"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("blanc"), list)
            and len(self.couleurs["blanc"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("dame_noir"), list)
            and len(self.couleurs["dame_noir"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("dame_blanc"), list)
            and len(self.couleurs["dame_blanc"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("damier_noir"), list)
            and len(self.couleurs["damier_noir"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("damier_blanc"), list)
            and len(self.couleurs["damier_blanc"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("bordure"), list)
            and len(self.couleurs["bordure"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("cases_possibles"), list)
            and len(self.couleurs["cases_possibles"]) == 3
        )
        assert (
            isinstance(self.couleurs.get("cases_deplacements"), list)
            and len(self.couleurs["cases_deplacements"]) == 3
        )

    @staticmethod
    def pseudo_aleatoire() -> str:
        return f"Joueur{random.randint(0, 999):03}"


def reglages_str(reglages: Reglages) -> str:
    return f"""# réglages du jeu
pseudo = \"{reglages.pseudo}\"
taille_damier = {reglages.taille_damier}
duree_animation = {reglages.duree_animation}

[couleurs]
noir = [ {", ".join([str(f) for f in reglages.couleurs["noir"]])} ]
blanc = [ {", ".join([str(f) for f in reglages.couleurs["blanc"]])} ]
dame_noir = [ {", ".join([str(f) for f in reglages.couleurs["dame_noir"]])} ]
dame_blanc = [ {", ".join([str(f) for f in reglages.couleurs["dame_blanc"]])} ]
damier_noir = [ {", ".join([str(f) for f in reglages.couleurs["damier_noir"]])} ]
damier_blanc = [ {", ".join([str(f) for f in reglages.couleurs["damier_blanc"]])} ]
bordure = [ {", ".join([str(f) for f in reglages.couleurs["bordure"]])} ]
cases_possibles = [ {", ".join([str(f) for f in reglages.couleurs["cases_possibles"]])} ]
cases_deplacements = [ {", ".join([str(f) for f in reglages.couleurs["cases_deplacements"]])} ]
"""


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


def configuration_serveur() -> ConfigurationServeur | None:
    fichier_conf = _root_pydames / "serveur.toml"

    if fichier_conf.exists():
        with open(fichier_conf, "rb") as f:
            return ConfigurationServeur(tomllib.load(f))
    else:
        with open(fichier_conf, "w", encoding="utf-8") as f:
            f.write(conf_defaut)
            print(
                f"Configuration par défaut écrite dans '{fichier_conf}'. Veuillez la mettre à jour."
            )


configuration = configuration_serveur()


def reglages() -> Reglages:
    fichier_reglages = _root_pydames / "reglages.toml"

    if fichier_reglages.exists():
        with open(fichier_reglages, "rb") as f:
            return Reglages(tomllib.load(f))
    else:
        with open(fichier_reglages, "w", encoding="utf-8") as f:
            r = Reglages(None)
            f.write(reglages_str(r))
            return r


def sauvegarder_reglages(reglages: Reglages):
    fichier_reglages = _root_pydames / "reglages.toml"

    with open(fichier_reglages, "w", encoding="utf-8") as f:
        f.write(reglages_str(reglages))
