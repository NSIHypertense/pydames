"use strict";

scripts_table.push(document.currentScript);

addEventListener("load", () => {
	scripts_table.forEach((script) => {
		const tbody = script.previousSibling;

		if (tbody != null && tbody.tagName == "TBODY") {
			const elements = Array.from(tbody.children);

			elements.forEach((tr) => {
				if (tr.tagName == "TR") {
					const td = tr.firstChild;

					if (td != null && td.tagName == "TD") {
						const a = td.firstChild;

						if (a != null && a.tagName == "A") {
							tr.style.cursor = "pointer";
							tr.addEventListener("click", () => a.click());
						}
					}
				}
			});
		}
	});
});
