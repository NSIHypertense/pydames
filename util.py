# utilités
import pathlib
import tomllib

conf_defaut = """# configuration du serveur pydames
[socket]
adresse = "0.0.0.0"       # affecter à "127.0.0.1" pour servir seulement sur la machine locale
port = 2332

[mysql]
hote = "localhost"        # adresse IP ou nom de domaine du serveur MySQL
utilisateur = "pydames"
mdp = "pydames"           # mot de passe
base = "pydames"          # nom de la base de données à utiliser
"""


class Couleurs:
    noir = (0, 0, 0)
    blanc = (255, 255, 255)
    vert = (0, 255, 0)


class ConfigurationServeur:
    def __init__(self, conf: dict):
        assert isinstance(conf, dict)
        assert "socket" in conf
        assert "mysql" in conf

        socket = conf["socket"]
        assert "adresse" in socket and isinstance(socket["adresse"], str)
        assert "port" in socket and isinstance(socket["port"], int)

        mysql = conf["mysql"]
        assert isinstance(mysql, dict)
        assert "hote" in mysql and isinstance(mysql["hote"], str)
        assert "utilisateur" in mysql and isinstance(mysql["utilisateur"], str)
        assert "mdp" in mysql and isinstance(mysql["mdp"], str)
        assert "base" in mysql and isinstance(mysql["base"], str)

        self.__socket = socket
        self.__mysql = mysql

    @property
    def socket(self) -> dict:
        return self.__socket

    @property
    def mysql(self) -> dict:
        return self.__mysql


root_pydames = pathlib.Path(__file__).resolve().parent


def resource(emplacement: str | pathlib.Path, octets: bool = False):
    return open(root_pydames / emplacement, mode="rb" if octets else "r")


fichier_conf = root_pydames / "serveur.toml"
configuration = None

if fichier_conf.exists():
    with open(fichier_conf, "rb") as f:
        configuration = ConfigurationServeur(tomllib.load(f))
else:
    with open(fichier_conf, "w") as f:
        f.write(conf_defaut)
        print(
            f"Configuration par défaut écrite dans '{fichier_conf}'. Veuillez la mettre à jour."
        )
