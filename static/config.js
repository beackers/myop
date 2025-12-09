function refreshConfig(csrf) {
    wrapper = document.getElementById("config");
    var config;
    fetch("/controlapi")
    .then (response => response.json())
    .then (config => {
        alert(JSON.stringify(config, null, 2));
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/controlapi";

    const incidentTitle = document.createElement("input");
    incidentTitle.type = "text";
    incidentTitle.name = "title";
    incidentTitle.placeholder = "Incident Title";
    incidentTitle.value = config.title;

    const chatEnabled = document.createElement("input");
    chatEnabled.type = "checkbox";
    chatEnabled.checked = (!!config.services && !!config.services.chat);
    chatEnabled.name = "chat";
    chatEnabled.value = "1";
    chatEnabled.id = "chat";
    const chatLabel = document.createElement("label");
    chatLabel.textContent = "Chat enabled?"
    chatLabel.htmlFor = "chat";

    const bulletinsOn = document.createElement("input");
    const bulletinsLabel = document.createElement("label");
    bulletinsOn.type = "checkbox";
    bulletinsOn.name = "bulletins";
    bulletinsOn.value = "1";
    bulletinsOn.checked = (!!config.services && !!config.services);
    bulletinsOn.id = "bulletins";
    bulletinsLabel.textContent = "Bulletins enabled?";
    bulletinsLabel.htmlFor = "bulletins";
    
    const csrfElement = document.createElement("input");
    csrfElement.type = "hidden";
    csrfElement.name = "csrf";
    csrfElement.value = csrf;

    const submit = document.createElement("input");
    submit.type = "submit";
    submit.textContent = "Save Config";

    var frag = document.createDocumentFragment();
    form.appendChild(incidentTitle);
    form.appendChild(chatLabel);
    form.appendChild(chatEnabled);
    form.appendChild(bulletinsLabel);
    form.appendChild(bulletinsOn);
    form.appendChild(csrfElement);
    form.appendChild(submit);
    frag.appendChild(form);
    wrapper.appendChild(frag);
    })
    .catch(err => alert(`something happened:\n${err}`));
}


function sendConfig() {
}
