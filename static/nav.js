function addANav() {
    const navdiv = document.getElementById("navdiv");
    const current = window.location.pathname;
    // change / add websites here!
    const navData = [
    {
        label: "tools",
        items: [
            { label: "home", value: "/" },
            { label: "bulletin board", value: "/bulletins" },
            { label: "chat", value: "/chat"}
        ]
    },
    {
        label: "you",
        items: [
            { label: "login", value: "/login" }
        ]
    },
    {
        label: "admin",
        items: [
            { label: "control", value: "/control" },
            { label: "add user", value: "/control/user/add" }
        ]
    }
    
    ];
    const hiddenNavData = [
                { label: "control : user", path: "/control/user/", pattern: /^\/control\/user\/\d+$/}
    ];

    const sel = document.createElement("select");

    // build each group
    for (const group of navData) {
        const optgroup = document.createElement("optgroup");
        optgroup.label = group.label;
        optgroup.id = group.label;

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
    // hidden menu for one-off navigation
    
    const hiddenMenuItem = hiddenNavData.find(item => item.pattern.test(window.location.pathname));
    if (hiddenMenuItem) {
        const group = document.createElement("optgroup");
        group.label = "current page";

        const opt = document.createElement("option");
        opt.textContent = hiddenMenuItem.label;
        opt.value = 1;
        opt.selected = true;

        group.appendChild(opt);
        sel.appendChild(group);
    };

    sel.addEventListener("change", () => {
        if (sel.value !== current) {
            const clean = DOMPurify.sanitize(sel.value);
            window.location.href = clean;
        };
    });

    navdiv.appendChild(sel);
}

// addANav();

// window.location.pathname = "/control";
// addANav();

// window.location.pathname = "/control/user/123";
// addANav();
