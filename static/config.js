function refreshConfig(csrf) {
    wrapper = document.getElementById("config");
    var config;
    fetch("/controlapi")
    .then (response => response.json())
    .then (config => {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/controlapi";

    const incidentTitle = document.createElement("input");
    incidentTitle.type = "text";
    incidentTitle.name = "title";
    incidentTitle.placeholder = "Incident Title";
    incidentTitle.value = config.title;
    const itBR = document.createElement("br");

    const chatEnabled = document.createElement("input");
    chatEnabled.type = "checkbox";
    chatEnabled.checked = (!!config.services && !!config.services.chat);
    chatEnabled.name = "chat";
    chatEnabled.value = "1";
    chatEnabled.id = "chat";
    const chatLabel = document.createElement("label");
    chatLabel.textContent = "Chat enabled?"
    chatLabel.htmlFor = "chat";
    const cBR = document.createElement("br");

    const bulletinsOn = document.createElement("input");
    const bulletinsLabel = document.createElement("label");
    bulletinsOn.type = "checkbox";
    bulletinsOn.name = "bulletins";
    bulletinsOn.value = "1";
    bulletinsOn.checked = (!!config.services && !!config.services.bulletins);
    bulletinsOn.id = "bulletins";
    bulletinsLabel.textContent = "Bulletins enabled?";
    bulletinsLabel.htmlFor = "bulletins";
    const bBR = document.createElement("br");
    
    const csrfElement = document.createElement("input");
    csrfElement.type = "hidden";
    csrfElement.name = "csrf";
    csrfElement.value = csrf;

    const submit = document.createElement("input");
    submit.type = "submit";
    submit.textContent = "Save Config";

    var frag = document.createDocumentFragment();
    form.appendChild(incidentTitle);
    form.appendChild(itBR);
    form.appendChild(chatLabel);
    form.appendChild(chatEnabled);
    form.appendChild(cBR);
    form.appendChild(bulletinsLabel);
    form.appendChild(bulletinsOn);
    form.appendChild(bBR);
    form.appendChild(csrfElement);
    form.appendChild(submit);
    frag.appendChild(form);
    wrapper.appendChild(frag);
    })
    .catch(err => alert(`something happened:\n${err}`));
}


function addDeleteBulletins() {
	const button = document.createElement("button");
	button.textContent = "Delete bulletins"
	button.onclick = function () {
		fetch("/bulletinsapi", {
			"method": "DELETE"
		});
	};
	const buttonwrapper = document.getElementById("deletebulletins")
	buttonwrapper.appendChild(button)
}
