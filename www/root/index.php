<?php
error_reporting(E_ALL);
$env = include '.env.php';
include 'bdd.php';
$bdd = bdd();

function verifierPydames() {
	global $env;

	$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	if (!$socket) {
		throw new Exception("Pas pu créer de socket");
	}

	$res = socket_connect($socket, "localhost", $env["socket"]["port"]);
	if (!$res) {
		return false;
	}

	socket_close($socket);
	return true;
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
	<meta charset="UTF-8">
	<title>pydames</title>
	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/picnic">
	<link rel="stylesheet" href="style.css">
</head>
<body>
	<nav>
		<a href="#" class="brand"><span>pydames</span></a>
		<div class="menu">
			<a href="index.php" class="pseudo button">Accueil</a>
		</div>
	</nav>
	<main>
		<article class="card">
			<header>
				<h3>Statut</h3>
			</header>
			<footer>
				<span><span class="statut label <?php print(verifierPydames() ? "success" : "error"); ?>"></span>Serveur pydames</span><br>
				<span><span class="statut label <?php print(verifierBdd($bdd) ? "success" : "error"); ?>"></span>Connexion MySQL</span>
			</footer>
		</article>
	</main>
</body>
</html>
