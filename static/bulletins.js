async function loadBulletins() {
    const container = document.getElementById("bulletinList");
    if (!container) return;

    try {
    const response = await fetch("/bulletinsapi");
    if (!response.ok) {
        container.textContent = "Error loading bulletins.";
        return;
    }

    const data = await response.json();
    const bulletins = data.bulletins || [];

    // Clear the container without nuking the element
    container.innerHTML = "";
    // container.replaceChildren();
    // newer method


    // Build a fragment for efficient DOM updates
    const frag = document.createDocumentFragment();

    bulletins.forEach(b => {
        const div = document.createElement("div");
        div.className = "bulletin";

        const title = document.createElement("h3");
        title.textContent = b.title || "(No title)";

        const body = document.createElement("p");
        body.textContent = b.body || "";

        const meta = document.createElement("div");
        meta.className = "bulletinMeta";

        const ts = new Date(b.timestamp).toLocaleString();
        const exp = b.expires ? new Date(b.expires).toLocaleString() : "N/A";
	const origin = b.origin || "unknown origin"

        meta.textContent = `Posted: ${ts} | Expires: ${exp}\nOriginating station: ${origin}`;

        div.appendChild(title);
        div.appendChild(body);
        div.appendChild(meta);

        frag.appendChild(div);
    });

    container.appendChild(frag);

    } catch (err) {
    container.textContent = "Network error while loading bulletins.";
    console.error(err);
    }
}
