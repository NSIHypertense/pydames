<?php
$env = include '.env.php';

function bdd() {
	global $env;
	static $mysqli = null;

	if ($mysqli === null) {
		$mysqli = new mysqli(
			$env['mysql']['hote'],
			$env['mysql']['utilisateur'],
			$env['mysql']['mdp'],
			$env['mysql']['base'],
			$env['mysql']['port']
		);

		if ($mysqli->connect_error) {
			die("Erreur de connexion : " . $mysqli->connect_error);
		}
	}

	return $mysqli;
}

function verifierBdd($mysqli) {
	if ($mysqli !== null && $mysqli->connect_errno == 0) {
		try {
			$mysqli->query('DO 1');
			return true;
		} catch (mysqli_sql_exception) {}
	}
	return false;
}
