<?php
error_reporting(E_ALL);
$env = include 'data/.env.php';
$fichier_salons = joindreChemins(__DIR__, 'data', 'salons.json');

class BddException extends Exception { }

function bdd(bool $connecter): mysqli|null {
	global $env;
	static $mysqli = null;

	if ($connecter && $mysqli === null) {
		$mysqli = new mysqli(
			$env['mysql']['hote'],
			$env['mysql']['utilisateur'],
			$env['mysql']['mdp'],
			$env['mysql']['base'],
			$env['mysql']['port']
		);

		if ($mysqli->connect_error) {
			throw new BddException($mysqli->connect_error);
		}
	}

	return $mysqli;
}

function verifierBdd(mysqli|null $mysqli): bool {
	if ($mysqli !== null && $mysqli->connect_errno == 0) {
		try {
			$mysqli->query('DO 1');
			return true;
		} catch (mysqli_sql_exception) {}
	}
	return false;
}

function verifierPydames(): bool {
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

function joindreChemins(...$chemins) {
    return preg_replace('~[/\\\\]+~', DIRECTORY_SEPARATOR, implode(DIRECTORY_SEPARATOR, $chemins));
}

function chargerSalons(): array {
	global $fichier_salons;
	if (file_exists($fichier_salons)) {
		$salons = json_decode(file_get_contents($fichier_salons), true);
		if ($salons === null) {
			return [];
		}
		return $salons;
	} else {
		file_put_contents($fichier_salons, "{}");
		return [];
	}
}

function sauvegarderSalons(array $salons) {
	global $fichier_salons;
	file_put_contents($fichier_salons, json_encode($salons));
}

function tablesBdd(mysqli $mysqli): array {
	$tables = [];

	$_tables = $mysqli->query("SHOW TABLES");
	if (!$_tables) {
		throw new BddException($mysqli->error);
	}

	while ($row = $_tables->fetch_array()) {
		$nom_table = $row[0];
		$compte = $mysqli->query("SELECT COUNT(*) FROM `$nom_table`");
		$tables[$nom_table] = $compte ? $compte->fetch_array()[0] : null;
	}

	return $tables;
}

function htmlTablesBdd(array $tables) {
	print('<ul class="liste-compacte">');
	foreach ($tables as $k => $v) {
		print("<li><strong>$k</strong> : $v</li>");
	}
	print('</ul>');
}

function query(array $a, array $b): string {
	$get = array_merge($_GET, $a);
	foreach ($b as $v) {
		unset($get[$v]);
	}
	return http_build_query($get);
}

function rechercheSql(mysqli $mysqli, string $sql, array $params, string $types): array {
	$req = $mysqli->prepare($sql);

	if (!$req)
		throw new BddException($mysqli->error);
	if ($types && $params)
		$req->bind_param($types, ...$params);
	if (!$req->execute())
		throw new BddException($req->error);

	$res = $req->get_result();
	$table = [];

	while ($ligne = $res->fetch_assoc()) {
		$table[] = $ligne;
	}

	$req->close();

	return $table;
}

function htmlRecherche(int $nombre) {
	$recherche = trim($_GET['joueur'] ?? "");
	$s = $nombre > 1 ? "s" : "";
	if ($recherche !== '') {
		print("<span><strong>$nombre</strong> résultat$s trouvé$s pour \"$recherche\"");
	}
}

function rechercheJoueurs(mysqli $mysqli, int|null $id_joueur = null): array {
	$recherche = trim($_GET['joueur'] ?? "");
	$params = [];
	$types = '';

	$sql_parties_gagnees = '
	SUM(
		CASE
			WHEN (parties.id_noir = equipes.id AND statistiques.score > adversaire.score) 
			OR (parties.id_blanc = equipes.id AND statistiques.score > adversaire.score)
			THEN 1 ELSE 0
		END
	)
	';
	$sql_parties_perdues = '
	SUM(
		CASE
			WHEN (parties.id_noir = equipes.id AND statistiques.score < adversaire.score) 
			OR (parties.id_blanc = equipes.id AND statistiques.score < adversaire.score)
			THEN 1 ELSE 0
		END
	)
	';

	$sql = "
	SELECT 
		classement.id,
		classement.rang,
		classement.nom,
		classement.parties_jouees,
		classement.parties_gagnees,
		classement.parties_perdues,
		classement.score_total,
		classement.dames_total,
		classement.premiere_partie,
		classement.derniere_partie
	FROM (
		SELECT 
			joueurs.id,
			DENSE_RANK() OVER (
				ORDER BY
					COALESCE(SUM(statistiques.score), 0) DESC,
					COALESCE($sql_parties_gagnees, 0) DESC,
					COALESCE($sql_parties_perdues, 0) ASC,
					COALESCE(SUM(statistiques.dames), 0) DESC,
					COALESCE(SUM(statistiques.pions_restants), 0) DESC,
					MD5(joueurs.nom) DESC
			) AS rang,
			joueurs.nom,
			COUNT(DISTINCT parties.id) AS parties_jouees,
			$sql_parties_gagnees AS parties_gagnees,
			$sql_parties_perdues AS parties_perdues,
			COALESCE(SUM(statistiques.score), 0) AS score_total,
			COALESCE(SUM(statistiques.dames), 0) AS dames_total,
			COALESCE(SUM(statistiques.pions_restants), 0) AS pions_restants_total,
			MIN(parties.debut) AS premiere_partie,
			MAX(parties.debut) AS derniere_partie
		FROM joueurs
		LEFT JOIN equipes ON equipes.id_joueur = joueurs.id
		LEFT JOIN parties ON parties.id_noir = equipes.id OR parties.id_blanc = equipes.id
		LEFT JOIN statistiques ON statistiques.id = equipes.id_statistiques
		LEFT JOIN statistiques AS adversaire ON adversaire.id = 
			CASE 
				WHEN parties.id_noir = equipes.id THEN parties.id_blanc
				WHEN parties.id_blanc = equipes.id THEN parties.id_noir
			END
		GROUP BY joueurs.id
	) AS classement
	";

	$where = 'WHERE';
	if ($recherche !== '') {
		$sql .= "$where classement.nom LIKE ? ";
		$params[] = "%$recherche%";
		$types .= 's';
		$where = 'AND';
	}
	if ($id_joueur !== null) {
		$sql .= "$where classement.id = ? ";
		$params[] = $id_joueur;
		$types .= 'i';
	}

	$sql .= '
	ORDER BY rang
	';

	return rechercheSql($mysqli, $sql, $params, $types);
}

function htmlRechercheJoueurs(array $joueurs) {
	htmlRecherche(sizeof($joueurs));

	print("<table class=\"full\"><thead><tr>
		<th>Rang</th>
		<th>Nom</th>
		<th>Parties jouées</th>
		<th>Parties gagnées</th>
		<th>Parties perdues</th>
		<th>Score total</th>
		<th>Dames totales</th>
		</tr></thead><tbody>");

	foreach ($joueurs as $i => $a) {
	$id = reset($a);
	$v = next($a);
		print("<tr>");
		print("<td><a href=\"?" . query(["id_joueur" => $id], []) . "\">#$v</a></td>");
		foreach (array_slice($a, 2, 6) as $v) {
			print("<td>$v</td>");
		}
		print("</tr>");
	}
	print("</tbody><script src=\"tr_clic.js\"></script></table>");
}

function rechercheParties(mysqli $mysqli): array {
	$recherche = trim($_GET['joueur'] ?? "");
	$params = [];
	$types = '';

	$sql = '
	SELECT
		parties.id,
		parties.debut,
		parties.fin,
		joueur_noir.nom AS joueur_noir,
		joueur_blanc.nom AS joueur_blanc,
		CASE
			WHEN statistiques_noir.score > statistiques_blanc.score THEN "Noir"
			WHEN statistiques_blanc.score > statistiques_noir.score THEN "Blanc"
			ELSE "Égalité"
		END AS gagnant,
		CASE
			WHEN statistiques_noir.score < statistiques_blanc.score THEN "Noir"
			WHEN statistiques_blanc.score < statistiques_noir.score THEN "Blanc"
			ELSE "Égalité"
		END AS perdant
	FROM parties
	LEFT JOIN equipes AS equipe_noir ON equipe_noir.id = parties.id_noir
	LEFT JOIN equipes AS equipe_blanc ON equipe_blanc.id = parties.id_blanc
	LEFT JOIN joueurs AS joueur_noir ON joueur_noir.id = equipe_noir.id_joueur
	LEFT JOIN joueurs AS joueur_blanc ON joueur_blanc.id = equipe_blanc.id_joueur
	LEFT JOIN statistiques AS statistiques_noir ON statistiques_noir.id = equipe_noir.id_statistiques
	LEFT JOIN statistiques AS statistiques_blanc ON statistiques_blanc.id = equipe_blanc.id_statistiques
	';

	if ($recherche !== "") {
		$sql .= 'WHERE joueur_noir.nom LIKE ? OR joueur_blanc.nom LIKE ?';
		array_push($params, "%$recherche%", "%$recherche%");
		$types .= 'ss';
	}

	$sql .= '
	ORDER BY parties.debut DESC
	';

	return rechercheSql($mysqli, $sql, $params, $types);
}

function htmlRechercheParties(array $parties) {
	htmlRecherche(sizeof($parties));

	print("<table class=\"full\"><thead><tr>
		<th>Début</th>
		<th>Fin</th>
		<th>Noir</th>
		<th>Blanc</th>
		<th>Gagnant</th>
		<th>Perdant</th>
		</tr></thead><tbody>");

	foreach ($parties as $a) {
		$id = reset($a);
		$v = next($a);
		print("<tr>");
		print("<td><a href=\"?" . query(["id_partie" => $id], []) . "\">$v</a></td>");
		foreach (array_slice($a, 2) as $v) {
			print("<td>$v</td>");
		}
		print("</tr>");
	}
	print("</tbody><script src=\"tr_clic.js\"></script></table>");
}

function joueur(mysqli $mysqli): array {
	if (!isset($_GET['id_joueur']))
		return [];

	$id_joueur = (int)$_GET['id_joueur'];

	return rechercheJoueurs($mysqli, $id_joueur);
}

function joueurEvolution(mysqli $mysqli): array {
	if (!isset($_GET['id_joueur']))
		return [];

	$id_joueur = (int)$_GET['id_joueur'];
	$params = [$id_joueur];
	$types = 'i';

	$sql = "
	SELECT 
		parties.fin,
		statistiques_joueur.score,
		statistiques_joueur.dames,
		statistiques_adversaire.pions_restants
	FROM equipes AS equipe_joueur
	LEFT JOIN parties ON parties.id_noir = equipe_joueur.id OR parties.id_blanc = equipe_joueur.id
	LEFT JOIN equipes AS equipe_adversaire ON (
		(parties.id_noir = equipe_joueur.id AND parties.id_blanc = equipe_adversaire.id) OR
		(parties.id_blanc = equipe_joueur.id AND parties.id_noir = equipe_adversaire.id)
	)
	LEFT JOIN statistiques AS statistiques_joueur ON statistiques_joueur.id = equipe_joueur.id_statistiques
	LEFT JOIN statistiques AS statistiques_adversaire ON statistiques_adversaire.id = equipe_adversaire.id_statistiques
	WHERE equipe_joueur.id_joueur = ?
	ORDER BY parties.fin ASC
	";

	return rechercheSql($mysqli, $sql, $params, $types);
}

function quickchartUrlEvolution(string $nom, array $evolution): string {
	$labels = [];
	$scores = [];
	$dames = [];
	$pions = [];

	foreach ($evolution as $partie) {
		$date = date('d/m/Y', strtotime($partie['fin']));
		$labels[] = $date;
		$scores[] = (int) $partie['score'];
		$dames[] = (int) $partie['dames'];
		$pions[] = (int) $partie['pions_restants'];
	}

	$graphique = [
		'type' => 'line',
		'data' => [
			'labels' => $labels,
			'datasets' => [
				[
					'label' => 'Score',
					'data' => $scores,
					'borderColor' => '#0074d9',
					'fill' => false
				],
				[
					'label' => 'Dames',
					'data' => $dames,
					'borderColor' => '#2ecc40',
					'fill' => false
				],
				[
					'label' => 'Pions restants',
					'data' => $pions,
					'borderColor' => '#ff851b',
					'fill' => false
				],
			]
		],
		'options' => [
			'title' => [
				'display' => true,
				'text' => $nom
			],
			'scales' => [
				'yAxes' => [[
					'ticks' => ['beginAtZero' => true]
				]]
			]
		]
	];

	$graphique_json = json_encode($graphique);
	$graphique_url = "https://quickchart.io/chart?c=" . urlencode($graphique_json);

	return $graphique_url;
}

function partiesJouees(mysqli $mysqli): array {
	if (!isset($_GET['id_joueur']))
		return [];

	$id_joueur = (int)$_GET['id_joueur'];
	$params = [];
	$types = 'i';

	$sql = '
	SELECT
		parties.id AS partie_id,
		parties.debut AS debut_partie,
		parties.fin AS fin_partie,
		statistiques_joueur.score AS score,
		statistiques_joueur.dames AS dames,
		CASE
			WHEN statistiques_joueur.score > statistiques_adversaire.score THEN "Gagnant"
			WHEN statistiques_joueur.score < statistiques_adversaire.score THEN "Perdant"
			ELSE "Égalité"
		END AS conclusion
	FROM equipes AS equipe_joueur
	LEFT JOIN parties ON parties.id_noir = equipe_joueur.id OR parties.id_blanc = equipe_joueur.id
	LEFT JOIN equipes AS equipe_adversaire ON (
		(parties.id_noir = equipe_joueur.id AND parties.id_blanc = equipe_adversaire.id) OR
		(parties.id_blanc = equipe_joueur.id AND parties.id_noir = equipe_adversaire.id)
	)
	LEFT JOIN statistiques AS statistiques_joueur ON statistiques_joueur.id = equipe_joueur.id_statistiques
	LEFT JOIN statistiques AS statistiques_adversaire ON statistiques_adversaire.id = equipe_adversaire.id_statistiques
	WHERE equipe_joueur.id_joueur = ?
	';

	$params[] = $id_joueur;

	return rechercheSql($mysqli, $sql, $params, $types);
}

function htmlJoueur(array $joueur, array $evolution, array $parties) {
	if ($joueur) {
		$infos = reset($joueur);

		print('<div class="flex two-1600 center">');

		print('<article class="fourth-1600">');
		print("<h4>Profil de {$infos['nom']}</h2>");
		print('<ul>');
		print("<li>Identifiant : <strong>{$infos['id']}</strong></li>");
		print("<li>Rang : <strong>#{$infos['rang']}</strong></li>");
		print("<li>Parties jouées : <strong>{$infos['parties_jouees']}</strong></li>");
		print("<li>Parties gagnées : <strong>{$infos['parties_gagnees']}</strong></li>");
		print("<li>Parties perdues : <strong>{$infos['parties_perdues']}</strong></li>");
		print("<li>Score total : <strong>{$infos['score_total']}</strong></li>");
		print("<li>Dames totales : <strong>{$infos['dames_total']}</strong></li>");
		print("<li>Première partie : <strong>{$infos['premiere_partie']}</strong></li>");
		print("<li>Dernière partie : <strong>{$infos['derniere_partie']}</strong></li>");
		print('</ul>');
		print('</article>');

		if ($evolution) {
			print('<article class="flex three-fourth-1600">');
			$url = quickchartUrlEvolution($infos['nom'], $evolution);
			print("<img src=\"$url\" alt=\"Graphique d'évolution du joueur\" style=\"width: 100%\">");
			print('</article>');
		}

		if ($parties) {
			print('<article class="full"><h4>Parties jouées</h4>');
			print('<table class="parties-jouees">');
			print('<thead><tr>');
			print('<th>Identifiant</th>');
			print('<th>Date de début</th>');
			print('<th>Date de fin</th>');
			print('<th>Score</th>');
			print('<th>Dames</th>');
			print('<th>Conclusion</th>');
			print('</tr></thead>');
			print('<tbody>');
			foreach ($parties as $p) {
				$v = reset($p);
				print('<tr><td><a href="?');
				print(query(["id_partie" => $v], ["id_joueur"]));
				print("\">$v</a>");
				foreach (array_slice($p, 1) as $v) {
					print("<td>$v</td>");
				}
				print('</a></td></tr>');
			}
			print('</tbody><script src="tr_clic.js"></script>');
			print('</table>');
			print('</article>');
		}
		print('</div>');
	}
}

function partie(mysqli $mysqli): array {
	if (!isset($_GET['id_partie']))
		return [];

	$id_partie = (int)$_GET['id_partie'];
	$params = [$id_partie];
	$types = 'i';

	$sql = '
	SELECT
		parties.id AS partie_id,
		parties.debut AS debut_partie,
		parties.fin AS fin_partie,
		joueur_noir.id AS id_noir,
		joueur_blanc.id AS id_blanc,
		joueur_noir.nom AS joueur_noir,
		joueur_blanc.nom AS joueur_blanc,
		statistiques_noir.score AS score_noir,
		statistiques_blanc.score AS score_blanc,
		statistiques_noir.dames AS dames_noir,
		statistiques_blanc.dames AS dames_blanc,
		statistiques_noir.pions_restants AS pions_noir,
		statistiques_blanc.pions_restants AS pions_blanc,
		CASE WHEN statistiques_noir.score > statistiques_blanc.score THEN 1 ELSE 0 END AS noir_gagnant,
		CASE WHEN statistiques_blanc.score > statistiques_noir.score THEN 1 ELSE 0 END AS blanc_gagnant
	FROM parties
	LEFT JOIN equipes AS equipe_noir ON equipe_noir.id = parties.id_noir
	LEFT JOIN equipes AS equipe_blanc ON equipe_blanc.id = parties.id_blanc
	LEFT JOIN joueurs AS joueur_noir ON joueur_noir.id = equipe_noir.id_joueur
	LEFT JOIN joueurs AS joueur_blanc ON joueur_blanc.id = equipe_blanc.id_joueur
	LEFT JOIN statistiques AS statistiques_noir ON statistiques_noir.id = equipe_noir.id_statistiques
	LEFT JOIN statistiques AS statistiques_blanc ON statistiques_blanc.id = equipe_blanc.id_statistiques
	WHERE parties.id = ?
	';

	return rechercheSql($mysqli, $sql, $params, $types);
}

function htmlPartie(array $partie) {
	if ($partie) {
		$infos = reset($partie);  // On récupère les infos de la partie actuelle
		$perdant_egalite = $infos['noir_gagnant'] == 1 || $infos['blanc_gagnant'] == 1;
		$perdant_egalite_texte = $perdant_egalite ? 'Perdant' : 'Égalité';
		$noir_texte = $infos['noir_gagnant'] === 1 ? 'Gagnant' : $perdant_egalite_texte;
		$noir_classe = $perdant_egalite ? ($infos['noir_gagnant'] === 1 ? 'success' : 'error') : 'warning';
		$blanc_texte = $infos['blanc_gagnant'] === 1 ? 'Gagnant' : $perdant_egalite_texte;
		$blanc_classe = $perdant_egalite ? ($infos['blanc_gagnant'] === 1 ? 'success' : 'error') : 'warning';
		$href_noir = query(["id_joueur" => $infos['id_noir']], ["id_partie"]);
		$href_blanc = query(["id_joueur" => $infos['id_blanc']], ["id_partie"]);

		print('<section>');

		print("<h4 style=\"padding: 0\">Partie #{$infos['partie_id']}</h4>");

		print('<ul>');
		print("<li>Date de début : <strong>{$infos['debut_partie']}</strong></li>");
		print("<li>Date de fin : <strong>{$infos['fin_partie']}</strong></li>");
		print("<li>Joueur noir : <strong>{$infos['joueur_noir']}</strong></li>");
		print("<li>Joueur blanc : <strong>{$infos['joueur_blanc']}</strong></li>");
		print('</ul>');

		print('</section>');
		print('<section class="flex two grow">');

		print('<div class="flex">');
		print('<article class="card">');
		print('<header>');
		print('<h3>Noir</h3>');
		print('</header>');
		print('<footer>');
		print("<h2 style=\"text-align: center; padding: 0 0 10px 0\"><span class=\"label $noir_classe\" style=\"margin: 0\">$noir_texte</span></h2>");
		print("<a href=\"?$href_noir\"><strong>{$infos['joueur_noir']}</strong></a><br>");
		print("<span>Score : <strong>{$infos['score_noir']}</strong></span><br>");
		print("<span>Dames : <strong>{$infos['dames_noir']}</strong></span><br>");
		print("<span>Pions restants : <strong>{$infos['pions_blanc']}</strong></span>");
		print('</footer>');
		print('</article>');
		print('</div>');

		print('<div class="flex">');
		print('<article class="card">');
		print('<header>');
		print('<h3>Blanc</h3>');
		print('</header>');
		print('<footer>');
		print("<h2 style=\"text-align: center; padding: 0 0 10px 0\"><span class=\"label $blanc_classe\" style=\"margin: 0\">$blanc_texte</span></h2>");
		print("<a href=\"?$href_blanc\"><strong>{$infos['joueur_blanc']}</strong></a><br>");
		print("<span>Score: <strong>{$infos['score_blanc']}</strong></span><br>");
		print("<span>Dames : <strong>{$infos['dames_blanc']}</strong></span><br>");
		print("<span>Pions restants : <strong>{$infos['pions_noir']}</strong></span>");
		print('</footer>');
		print('</article>');
		print('</div>');

		print('</section>');
	}
}

function htmlSalons(array $salons) {
	global $env;

	$salons_complets = [];
	$salons_incomplets = [];

	foreach ($salons as $k => $v) {
		if (sizeof($v) == 2) {
			$salons_complets[$k] = $v;
		} else {
			$salons_incomplets[$k] = $v;
		}
	}

	if (sizeof($salons_complets) != 0) {
		print('<span>Complets :</span><ul class="liste-compacte">');
		foreach ($salons_complets as $k => $v) {
			$joueurs = sizeof($v);
			$q = query(["id_salon" => $k], []);

			if ($env["flux"]["actif"]) print("<a href=\"?$q\">");
			print("<li><strong>$k</strong> ($joueurs joueurs)</li>");
			if ($env["flux"]["actif"]) print("</a>");
		}
		print('</ul>');
	}

	if (sizeof($salons_incomplets) != 0) {
		print('<span>Incomplets :</span><ul class="liste-compacte">');
		foreach ($salons_incomplets as $k => $v) {
			$joueurs = sizeof($v);
			print("<li><strong>$k</strong> ($joueurs joueurs)</li>");
		}
		print('</ul>');
	}
}

function joueurId(mysqli $mysqli, string $nom_joueur): int|null {
	$params = [$nom_joueur];
	$types = 's';
	$sql = 'SELECT id FROM joueurs WHERE nom = ? LIMIT 1';

	$res = rechercheSql($mysqli, $sql, $params, $types);

	return $res ? (int)$res[0]['id'] : null;
}

function htmlSalon(array $salons, mysqli $mysqli) {
	if (!isset($_GET['id_salon']))
		return [];

	$code = $_GET['id_salon'];
	$joueurs = $salons[$code];
	$joueur1 = reset($joueurs);
	$joueur2 = next($joueurs);

	$id_joueur1 = joueurId($mysqli, $joueur1);
	$id_joueur2 = joueurId($mysqli, $joueur2);

	$q1 = query(["id_joueur" => $id_joueur1], ["id_salon"]);
	$q2 = query(["id_joueur" => $id_joueur2], ["id_salon"]);

	print('<section class="flux flex two">');

	print('<div class="flex">');
	print('<article class="card">');
	print('<header>');
	print("<a href=\"?$q1\"><h3>$joueur1</h3></a>");
	print('</header>');
	print('<footer>');
	print("<img data-flux=\"$code/$joueur1\">");
	print('</footer>');
	print('</article>');
	print('</div>');

	print('<div class="flex">');
	print('<article class="card">');
	print('<header>');
	print("<a href=\"?$q2\"><h3>$joueur2</h3></a>");
	print('</header>');
	print('<footer>');
	print("<img data-flux=\"$code/$joueur2\">");
	print('</footer>');
	print('</article>');
	print('</div>');

	print('</section>');
}


try {
	bdd(true);
} catch (Exception $e) {
	error_log($e);
}
