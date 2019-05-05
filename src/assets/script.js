var butClaimLab = document.getElementById('claimLab');
if(butClaimLab != null) {
    butClaimLab.addEventListener('click', claimLabJS);
}

var butClaimFrontend = document.getElementById('claimFrontend');
if(butClaimFrontend != null) {
    butClaimFrontend.addEventListener('click', claimFrontendJS);
}

function claimFrontendJS(eventobj) {
    axios.get('/octp/claimfrontend')
    .then(function (response) {
        console.log(response);
        if (response.data.error != "") {
            alert(response.data.error);
            return
        }

        location.reload();
    })
    .catch(function (error) {
        alert("Failed to claim a frontend for you..")
    })
    .then(function () {
    // always executed
    });
}

function claimLabJS(eventobj) {
    axios.get('/octp/claimlab')
    .then(function (response) {
        console.log(response);
        if (response.data.error != "") {
            alert(response.data.error);
            return
        }

        location.reload();
    })
    .catch(function (error) {
        alert("Failed to claim a lab for you..")
    })
    .then(function () {
    // always executed
    });
}
