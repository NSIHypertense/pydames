CREATE TABLE IF NOT EXISTS jeux(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT
);

CREATE TABLE IF NOT EXISTS joueurs(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    nom VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS statistiques(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    score INT NOT NULL,
    dames INT NOT NULL,
    pions_restants INT NOT NULL
);

CREATE TABLE IF NOT EXISTS equipes(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_joueur INT NOT NULL,
    id_statistiques INT NOT NULL,
    FOREIGN KEY(id_joueur) REFERENCES joueurs(id),
    FOREIGN KEY(id_statistiques) REFERENCES statistiques(id)
);

CREATE TABLE IF NOT EXISTS parties(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_jeu INT NOT NULL,
    id_noir INT NOT NULL,
    id_blanc INT NOT NULL,
    debut DATETIME,
    fin DATETIME,
    FOREIGN KEY(id_jeu) REFERENCES jeux(id),
    FOREIGN KEY(id_noir) REFERENCES equipes(id),
    FOREIGN KEY(id_blanc) REFERENCES equipes(id)
);
