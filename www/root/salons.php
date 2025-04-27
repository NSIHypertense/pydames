<?php
include 'util.php';

header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');


function creerSalon($code) {
	$salons = chargerSalons();
	if (!isset($salons[$code])) {
		$salons[$code] = [];
		sauvegarderSalons($salons);
	}
}

function supprimerSalon($code) {
	$salons = chargerSalons();
	if (isset($salons[$code])) {
		unset($salons[$code]);
		sauvegarderSalons($salons);
	}
}

function ajouterJoueur($code_salon, $nom_joueur) {
	$salons = chargerSalons();
	if (isset($salons[$code_salon])) {
		if (!in_array($nom_joueur, $salons[$code_salon])) {
			$salons[$code_salon][] = $nom_joueur;
			sauvegarderSalons($salons);
		}
	}
}

function enleverJoueur($code_salon, $nom_joueur) {
	$salons = chargerSalons();
	if (isset($salons[$code_salon])) {
		$k = array_search($non_joueur, $salons[$code_salon]);
		if ($k !== false) {
			unset($salons[$code_salon][$k]);
			sauvegarderSalons($salons);
		}
	}
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
	print(json_encode(chargerSalons()));
} else if ($_SERVER['REQUEST_METHOD'] === 'POST') {
	$donnees = json_decode(file_get_contents('php://input'), true);

	if (!isset($donnees['action'])) {
		http_response_code(400);
		print("aucune action donnée");
		exit();
	}

	$action = $donnees['action'];

	switch ($action) {
	case "creer_salon":
		$code = $donnees['code_salon'];
		creerSalon($code);
		break;
	case "supprimer_salon":
		$code = $donnees['code_salon'];
		supprimerSalon($code);
		break;
	case "ajouter_joueur":
		$code_salon = $donnees['code_salon'];
		$nom_joueur = $donnees['nom_joueur'];
		ajouterJoueur($code_salon, $nom_joueur);
		break;
	case "enlever_joueur":
		$code_salon = $donnees['code_salon'];
		$nom_joueur = $donnees['nom_joueur'];
		enleverJoueur($code_salon, $nom_joueur);
		break;
	default:
		http_response_code(400);
		print("action invalide");
		break;
	}
}
