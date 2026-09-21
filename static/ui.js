// Duplicates a parameter, this is triggered by the interface for parameters that have 'multiple' set to true, after pressing the 'add more' button
function duplicateParameter(id) {
    var param = document.getElementById(id);
    if (param === null) {
        console.error("Parameter " + id + " not found");
        return;
    }
    var expansionSpace = document.getElementById("expspace_" + id);
    if (expansionSpace === null) {
        console.error("Expansion space for parameter " + id + " not found");
        return;
    }

    var newparam = param.cloneNode(true);
    newparam.id = newparam.id + "_DUP" + Math.random().toString(36).slice(2, 10);

    if ("value" in newparam) {
        newparam.value = "";
    }

    expansionSpace.appendChild(newparam);
    expansionSpace.insertAdjacentHTML("beforeend", '<button type="button" onClick="document.getElementById(\'' + newparam.id + '\').remove(); this.remove()">- Remove above field</button>');
}
