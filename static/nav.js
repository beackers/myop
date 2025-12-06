function addANav() {
    const navdiv = document.getElementById("navdiv");
    const current = window.location.pathname;
	var acceptablePaths = [];

    // change / add websites here!
    const navData = [
	{
		label: "THIS OP",
		items: [
			{ label: "home", value: "/" },
			{ label: "BULLETINS", value: "/bulletins" },
			{ label: "CHAT", value: "/chat"}
		]
	},
	{
		label: "admin",
		items: [
			{ label: "control", value: "/control" }
		]
	}
	
    ];

    const sel = document.createElement("select");

    // build each group
    for (const group of navData) {
        const optgroup = document.createElement("optgroup");
        optgroup.label = group.label;

        // build each option inside the group
        for (const item of group.items) {
            const opt = document.createElement("option");
            opt.textContent = item.label;
            opt.value = item.value;

            // auto-select the page you’re on
            if (item.value === current) {
                opt.selected = true;
            }

            optgroup.appendChild(opt);
			acceptablePaths.push(item.value);
        }

        sel.appendChild(optgroup);
    }

    sel.addEventListener("change", () => {
        if (sel.value !== current && acceptablePaths.includes(sel.value)) {
            window.location.href = sel.value;
        }
    });

    navdiv.appendChild(sel);
}
