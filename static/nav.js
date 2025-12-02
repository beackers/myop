function addANav() {
    const navdiv = document.getElementById("navdiv");
    const current = window.location.pathname;

    // change / add websites here!
    const navData = [
        {
            label: "important",
            items: [
                { label: "home", value: "/" },
                { label: "beliefs", value: "/beliefs" }
            ]
        },
        {
            label: "fun stuff",
            items: [
                { label: "drawings", value: "/drawings" }
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
        }

        sel.appendChild(optgroup);
    }

    sel.addEventListener("change", () => {
        if (sel.value !== current) {
            window.location.href = sel.value;
        }
    });

    navdiv.appendChild(sel);
}
