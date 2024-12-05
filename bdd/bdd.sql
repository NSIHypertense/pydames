DROP TABLE IF EXISTS joueur;
CREATE TABLE joueur(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    nom VARCHAR(30) NOT NULL
);

DROP TABLE IF EXISTS jeu;
CREATE TABLE jeu(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT
);

DROP TABLE IF EXISTS partie;
CREATE TABLE partie(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_jeu INT NOT NULL,
    id_noir INT NOT NULL,
    id_blanc INT NOT NULL,
    debut DATETIME,
    fin DATETIME,
    FOREIGN KEY(id_jeu) REFERENCES jeu(id_jeu),
    FOREIGN KEY(id_noir) REFERENCES equipe(id_noir),
    FOREIGN KEY(id_blanc) REFERENCES equipe(id_blanc)
);

DROP TABLE IF EXISTS equipe;
CREATE TABLE equipe(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    id_joueur INT NOT NULL,
    id_statistiques INT NOT NULL,
    FOREIGN KEY(id_joueur) REFERENCES joueur(id_joueur),
    FOREIGN KEY(id_statistiques) REFERENCES statistiques(id_statistiques)
);

DROP TABLE IF EXISTS statistiques;
CREATE TABLE statistiques(
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    score INT NOT NULL,
    dames INT NOT NULL,
    pions_restants INT NOT NULL
);