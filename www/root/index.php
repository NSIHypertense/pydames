<?php
$env = include 'data/.env.php';
include 'util.php';
$bdd = bdd(false);
$statut_bdd = verifierBdd($bdd);
if ($statut_bdd) {
	$tables = tablesBdd($bdd);
}
?>
<!DOCTYPE html>
<html lang="fr">
<head>
	<meta charset="UTF-8">
	<title>pydames</title>
	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/picnic">
	<link rel="stylesheet" href="style.css">
	<script src="inputs.js"></script>
	<script src="flux.js" data-actif="<?php print($env["flux"]["actif"]) ?>" data-port="<?php print($env["flux"]["port"]) ?>"></script>
	<script>const scripts_table = [];</script>
	<?php if (!isset($_GET['id_joueur']) && !isset($_GET['id_partie']) && !isset($_GET['id_salon'])) { print('<meta http-equiv="refresh" content="10" >'); } ?>
</head>
<body>
	<nav>
		<a href="#" class="brand"><span>pydames</span></a>
		<div class="menu">
			<a href="https://github.com/NSIHypertense/pydames" class="pseudo button">
				<img class="logo" src="https://cdn.simpleicons.org/github">
				GitHub
			</a>
		</div>
	</nav>
	<main>
		<h2>Tableau de bord</h2>
		<section class="flex three-1200 grow">
			<div class="flex">
				<article class="card">
					<header>
						<h3>Statut</h3>
					</header>
					<footer>
						<span><span class="statut label <?php print(verifierPydames() ? "success" : "error") ?>"></span>Serveur pydames (:<?php print($env["socket"]["port"]) ?>)<br></span>
						<span style="display: none"><span class="statut label" id="statutFlux"></span>Flux WebSocket (:<?php print($env["flux"]["port"]) ?>)<br></span>
						<span><span class="statut label <?php print($statut_bdd ? "success" : "error") ?>"></span>Connexion MySQL (<?php print($env["mysql"]["hote"] . ":" . $env["mysql"]["port"]) ?>)</span>
					</footer>
				</article>
				</div>
			<div class="flex">
				<article class="card">
					<header>
						<h3>Tables</h3>
					</header>
					<footer>
						<?php if($statut_bdd) { htmlTablesBdd($tables); } else { print("<span>Déconnecté de la base de données.</span>"); } ?>
					</footer>
				</article>
			</div>
			<div class="flex">
				<article class="card">
					<header>
						<h3>Salons</h3>
					</header>
					<footer>
						<?php htmlSalons(chargerSalons()) ?>
					</footer>
				</article>
			</div>
			<div class="flex full">
				<article class="card">
					<header>
						<h3>Recherche</h3>
					</header>
					<footer>
						<form method="get">
							<input type="text" id="input_joueur" name="joueur" placeholder="Nom d'un joueur..." />
							<div style="text-align: center">
								<input class="fourth" type="submit" value="Rechercher" />
							</div>
						</form>
					</footer>
				</article>
			</div>
			<div class="flex">
				<article class="card">
					<header>
						<h3>Joueurs</h3>
					</header>
					<footer>
						<div style="max-height: 200vh; overflow: auto">
							<?php if ($statut_bdd) { htmlRechercheJoueurs(rechercheJoueurs($bdd)); } else { print("<span>Déconnecté de la base de données.</span>"); } ?>
						</div>
					</footer>
				</article>
			</div>
			<div class="flex">
				<article class="card">
					<header>
						<h3>Parties</h3>
					</header>
					<footer>
						<div style="max-height: 200vh; overflow: auto">
							<?php if ($statut_bdd) { htmlRechercheParties(rechercheParties($bdd)); } else { print("<span>Déconnecté de la base de données.</span>"); } ?>
						</div>
					</footer>
				</article>
			</div>
		</section>
		<div class="modal">
			<input id="modal_joueur" type="checkbox" <?php if (isset($_GET['id_joueur'])) print("checked"); ?> />
			<a class="overlay" href="?<?php print(query([], ["id_joueur"])) ?>"></a>
			<article>
				<header>
					<h3>Joueur</h3>
				</header>
				<section>
					<?php htmlJoueur(joueur($bdd), joueurEvolution($bdd), partiesJouees($bdd)) ?>
				</section>
				<footer>
					<div style="float: right">
						<a class="button" href="?<?php print(query([], ["id_joueur"])) ?>">Ok</a>
					</div>
				</footer>
			</article>
		</div>
		<div class="modal">
			<input id="modal_partie" type="checkbox" <?php if (isset($_GET['id_partie'])) print("checked"); ?> />
			<a class="overlay" href="?<?php print(query([], ["id_partie"])) ?>"></a>
			<article>
				<header>
					<h3>Partie</h3>
				</header>
				<section>
					<?php htmlPartie(partie($bdd)) ?>
				</section>
				<footer>
					<div style="float: right">
						<a class="button" href="?<?php print(query([], ["id_partie"])) ?>">Ok</a>
					</div>
				</footer>
			</article>
		</div>
		<div class="modal">
			<input id="modal_salon" type="checkbox" <?php if (isset($_GET['id_salon'])) print("checked"); ?> />
			<a class="overlay" href="?<?php print(query([], ["id_salon"])) ?>"></a>
			<article>
				<header>
					<h3>Salon</h3>
				</header>
				<section>
					<?php htmlSalon(chargerSalons(), $bdd) ?>
				</section>
				<footer>
					<div style="float: right">
						<a class="button" href="?<?php print(query([], ["id_salon"])) ?>">Ok</a>
					</div>
				</footer>
			</article>
		</div>
	</main>
</body>
</html>
