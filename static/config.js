function refreshConfig() {
    currConfigContainer = document.getElementById("currConfig");
    fetch("/configapi")
    .then (response) => {
        response.json();
    }
    .then (json) => {
        console.log(json);
    };
}
function sendConfig() {
}
