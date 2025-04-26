# module du site web PHP

import http.client
import os
from pathlib import Path
import shutil
import stat
import subprocess
from tempfile import NamedTemporaryFile
import time
import traceback
import urllib.request
from zipfile import ZipFile


class Php:
    @staticmethod
    def telecharger(destination: Path) -> Path | None:
        if os.name != "nt":
            print(
                "[PHP] le système d’exploitation n’est pas Windows, donc PHP ne sera pas téléchargé."
            )
            return None

        if not destination.is_dir():
            print(
                f"[PHP] la destination du téléchargement n'existe pas : '{destination}'"
            )
            return None

        url = "https://windows.php.net/downloads/releases/php-8.4.6-nts-Win32-vs17-x86.zip"
        print(f"[PHP] téléchargement de '{url}'")

        with NamedTemporaryFile(delete=False, buffering=0) as fp:
            print(f"[PHP] archive temporaire : '{fp.name}'")
            try:
                with urllib.request.urlopen(url) as res:
                    while True:
                        chunk = res.read(8192)
                        if not chunk:
                            break
                        fp.write(chunk)
            except Exception:
                print("[PHP] erreur pendant le téléchargement")
                print(traceback.format_exc())

            tmp = Path(fp.name)

        print(f"[PHP] extraction dans '{destination}'")
        with ZipFile(tmp) as zip:
            zip.extractall(destination)
        tmp.unlink()

        print("[PHP] extrait.")

        php = destination / "php.exe"
        php.chmod(php.stat().st_mode | stat.S_IEXEC)

        assert php.is_file()
        return php

    @staticmethod
    def trouver(serveur: Path | None) -> Path | None:
        if serveur:
            php = serveur / "php.exe"
            if php.is_file():
                return php
            php = serveur / "php"
            if php.is_file():
                return php

        if (php := shutil.which("php.exe")) or (php := shutil.which("php")):
            php = Path(php)
            print(f"[PHP] trouvé : '{php}'")
            return php

    @staticmethod
    def generer_env(fichier, configuration: dict):
        contenu = f"""<?php
//
// NE PAS PARTAGER CE FICHIER
//
return [
    'socket' => [
        'port' => {configuration.socket["port"]}
    ],
    'mysql' => [
        'hote' => '{configuration.mysql["hote"]}',
        'port' => {configuration.mysql["port"]},
        'utilisateur' => '{configuration.mysql["utilisateur"]}',
        'mdp' => '{configuration.mysql["mdp"]}',
        'base' => '{configuration.mysql["base"]}'
    ]
];
"""
        fichier.write(contenu)

    @staticmethod
    def lancer(
        executable_php: Path,
        php_config: Path,
        www: Path,
        adresse: str,
        port: int,
    ) -> subprocess.Popen | None:
        if not executable_php.is_file():
            print(
                f"[PHP] l'exécutable php n'est pas installé à l'emplacement donné : '{executable_php}'"
            )
            return None
        executable_php = executable_php.resolve()

        if not www.is_dir():
            print("[PHP] le répertoire du site n'existe pas :", www)
            return None
        www = www.resolve()

        php_config.resolve()
        php_config = php_config if php_config.is_dir() else php_config.parent

        print("[PHP] lancement du serveur local...")
        proc = subprocess.Popen(
            [
                str(executable_php),
                "-S",
                f"{adresse}:{port}",
                "-c",
                str(php_config),
                "-t",
                str(www),
            ],
            cwd=php_config,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(f"[PHP] arguments : {proc.args}")

        e = None
        for i in range(10):
            try:
                conn = http.client.HTTPConnection(adresse, port, timeout=1)
                conn.request("GET", "/")
                res = conn.getresponse()
                if res.status == 200:
                    print(f"[PHP] serveur lancé sur http://{adresse}:{port}")
                    return proc
            except Exception as _e:
                e = _e
            time.sleep(0.5)

        if e:
            try:
                raise e
            except Exception:
                print("[PHP] erreur")
                print(traceback.format_exc())

        print("[PHP] le serveur n'a pas répondu à temps.")
        proc.terminate()

        return None

    @staticmethod
    def attendre(processus: subprocess.Popen):
        while processus and not processus.poll():
            for ligne in processus.stdout:
                print(f"[PHP] {ligne.decode('utf-8')}", end="")

    @staticmethod
    def arreter(processus: subprocess.Popen):
        if processus or not processus.poll():
            print("[PHP] arrêt du serveur...")
            try:
                processus.terminate()
                processus.wait(timeout=5)
            except Exception:
                processus.kill()
