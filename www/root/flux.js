const self = document.currentScript;

addEventListener("load", () => {
    const MARQUEUR = new TextEncoder().encode("FLUX_EOF");
    const TAILLE_MARQUEUR = MARQUEUR.length;

	const PORT = self.getAttribute("data-port");
	const ACTIF = self.getAttribute("data-actif");

	if (PORT == null) {
		console.error("Aucun port donné");
		return;
	}
	
	function verifierFlux() {
		return new Promise((resolve) => {
			const _ws = new WebSocket(`ws://localhost:${PORT}`);
			const timeout = 3000;

			const timer = setTimeout(() => {
				_ws.close();
				resolve(false);
			}, timeout);

			_ws.onopen = () => {
				clearTimeout(timer);
				_ws.close();
				resolve(true);
			};

			_ws.onerror = () => {
				clearTimeout(timer);
				resolve(false);
			};
		});
	}

	statutFlux = document.getElementById("statutFlux");
	statutFlux.parentNode.style.removeProperty("display");

	if (ACTIF === "1") {
		verifierFlux().then((res) => statutFlux.classList.add(res ? "success" : "error"));
	} else {
		statutFlux.classList.add("error");
		return;
	}

    document.querySelectorAll("img[data-flux]").forEach(img => {
        const fluxId = img.getAttribute("data-flux");
        const ws = new WebSocket(`ws://localhost:${PORT}`);
        
        let buffer = new Uint8Array(0);
        let lecteur = new FileReader();
        let attente = false;

        ws.binaryType = 'arraybuffer';

        ws.onopen = () => {
            console.log(`Connexion WebSocket ouverte pour ${fluxId}`);
            ws.send(fluxId);
        };

        lecteur.onload = () => {
            img.src = lecteur.result;
            if (img._srcPre) {
                URL.revokeObjectURL(img._srcPre);
            }
            img._srcPre = lecteur.result;
            attente = false;
            traiter();
        };

        lecteur.onerror = () => {
            console.error("Erreur de lecture du blob");
            attente = false;
        };

        function traiter() {
            if (attente) return;

            const index = trouverMarqueur(buffer, MARQUEUR);
            if (index !== -1) {
                const jpegData = buffer.slice(0, index);
                buffer = buffer.slice(index + TAILLE_MARQUEUR);

                if (jpegData.length > 0) {
                    const blob = new Blob([jpegData], { type: 'image/jpeg' });
                    attente = true;
                    lecteur.readAsDataURL(blob);
                }

                if (buffer.length > TAILLE_MARQUEUR) {
                    setTimeout(traiter, 0);
                }
            }
        }

        function trouverMarqueur(buf, marqueur) {
            const premierOctet = marqueur[0];
            for (let i = 0; i <= buf.length - marqueur.length; i++) {
                if (buf[i] === premierOctet) {
                    let correspondance = true;
                    for (let j = 1; j < marqueur.length; j++) {
                        if (buf[i + j] !== marqueur[j]) {
                            correspondance = false;
                            break;
                        }
                    }
                    if (correspondance) return i;
                }
            }
            return -1;
        }

        ws.onmessage = (event) => {
            if (!(event.data instanceof ArrayBuffer)) {
                console.warn("Reçu des données non-binaires");
                return;
            }

            const donnees = new Uint8Array(event.data);
            const bufferTemp = new Uint8Array(buffer.length + donnees.length);
            bufferTemp.set(buffer);
            bufferTemp.set(donnees, buffer.length);
            buffer = bufferTemp;

            traiter();
        };

        ws.onerror = (error) => {
            console.error("Erreur WebSocket :", error);
        };

        ws.onclose = () => {
            console.log("Connexion WebSocket fermée");
        };

        img._ws = ws;
    });
});

addEventListener("beforeunload", () => {
    document.querySelectorAll("img[data-flux]").forEach(img => {
        if (img._ws)
			img._ws.close();
        if (img._srcPre)
			URL.revokeObjectURL(img._srcPre);
    });
});

