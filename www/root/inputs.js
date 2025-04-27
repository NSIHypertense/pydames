function sauvegarderInputs() {
    const inputs = document.querySelectorAll("input");
    
    inputs.forEach(input => {
        if (input.name && (input.type === "checkbox" || input.type === "radio")) {
            localStorage.setItem(input.name, input.checked);
        } else if (input.id && input.type === "text") {
            localStorage.setItem(input.id, input.value);
        }
    });
}

function restaurerInputs() {
    const inputs = document.querySelectorAll("input");
    
    inputs.forEach(input => {
        if (input.name && (input.type === "checkbox" || input.type === "radio")) {
            input.checked = JSON.parse(localStorage.getItem(input.name)) || false;
        } else if (input.id && input.type === "text") {
            input.value = localStorage.getItem(input.id) || "";
        }
    });
}


addEventListener("load", function() {
	restaurerInputs();
	document.querySelectorAll("input").forEach(input => {
		input.addEventListener("change", sauvegarderInputs);
	});
});
