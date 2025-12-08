function refreshConfig() {
    currConfigContainer = document.getElementById("currConfig");
    var config;
    fetch("/configapi")
    .then (response) => {
        response.json();
    }
    .then (json) => {
        config = json;
    };
}
function sendConfig() {
}
