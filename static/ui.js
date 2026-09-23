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
    //note: id differs, but 'name' remains the same for all duplicates, we can have multiple equally-named fields in the HTTP POST request

    if ("value" in newparam) {
        newparam.value = "";
    }

    expansionSpace.appendChild(newparam);

    var toggleeditor = document.getElementById("toggleeditor_" + id);
    if (toggleeditor !== null) {
        var toggleeditor_new = toggleeditor.cloneNode(true);
        toggleeditor_new.id = "toggleeditor_" + newparam.id
        expansionSpace.appendChild(toggleeditor_new);
        expansionSpace.insertAdjacentHTML("beforeend", '<button type="button" class="remove" title="remove this field" onClick="document.getElementById(\'' + newparam.id + '\').remove(); document.getElementById(\'toggleeditor_' + newparam.id + '\').remove(); this.remove()">❌</button>');
    } else {
        expansionSpace.insertAdjacentHTML("beforeend", '<button type="button" class="remove" title="remove this field" onClick="document.getElementById(\'' + newparam.id + '\').remove(); this.remove()">❌</button>');
    }
}

function toggleEditor(id) {
    var param = document.getElementById(id);
    if (param === null) {
        console.error("Parameter " + id + " not found");
        return;
    }
    if (("type" in param) && (param.type == "file")) {
        var required = "";
        if ("required" in param) {
            required = " required";
        }
        param.outerHTML = '<textarea id="' + param.id + '"' + ' name="' + param.name + '"' + required + ' title="' + param.title + '"></textarea><div id="filename_' + id + '" class="filename"><label for="filename_' + id + '">Filename:</label> <input type="text"  name="' + param.name + '_filename" title="The name to give the file whose contents are edited above"></div>'
        document.getElementById("toggleeditor_" + id).innerHTML = "📎";
    } else {
        param.outerHTML = '<input type="file" id="' + param.id + '"' + ' name="' + param.name + '"' + required + ' title="' + param.title + '">'
        document.getElementById("toggleeditor_" + id).innerHTML = "🖊";
        document.getElementById("filename_" + id).remove();
    }
}
