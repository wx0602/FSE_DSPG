(function () {
    var nameInput = document.querySelector('.name'),
        btnSave = document.querySelector('button.save'),
        assignedActivities = document.querySelector('#assignedActivities'),
        availableActivities = document.querySelector('#availableActivities'),
        assingInput = document.querySelector('#assignInput'),
        unAssignInput = document.querySelector('#unAssignInput'),
        availableActivitiesMap = new Map(),
        assignedActivitiesMap = new Map();

    if (assingInput != null) {
        assingInput.addEventListener("keyup", function (e) {
            let value = assingInput.value.toLowerCase();
            document.querySelectorAll('#availableActivities>li').forEach(x => x.classList.remove("d-none"));
            if (value === "") {
                return;
            }
            document.querySelectorAll('#availableActivities>li').forEach(x => {
                if (!x.getAttribute("data-name").toLowerCase().includes(value)) {
                    x.classList.add("d-none");
                }
            });
        }, false);
    }
    if (unAssignInput != null) {
        unAssignInput.addEventListener("keyup", function (e) {
            let value = unAssignInput.value.toLowerCase();
            document.querySelectorAll('#assignedActivities>li').forEach(x => x.classList.remove("d-none"));
            if (value === "") {
                return;
            }
            document.querySelectorAll('#assignedActivities>li').forEach(x => {
                if (!x.getAttribute("data-name").toLowerCase().includes(value)) {
                    x.classList.add("d-none");
                }
            });
        }, false);
    }
    if (availableActivities !== null) {
        for (var i = 0; i < availableActivities.children.length; i++) {
            availableActivitiesMap.set(
                +availableActivities.children[i].getAttribute('data-activityid'),
                availableActivities.children[i]
            )
        }
    }

    function checkActivityInputs() {
        if (nameInput.value.trim() == "") {
            $('#errors').removeClass("d-none");
            $('#type-error').text("Pole nazwa jest puste");
            return false;
        }
        return true;
    }

    if (document.querySelector('.to-assign') != null) {
        document.querySelector('.to-assign').addEventListener('click', function (evt) {
            var id = +evt.target.getAttribute('data-activityid');
            if (availableActivitiesMap.get(id) !== undefined) {
                assignedActivitiesMap.set(id, availableActivitiesMap.get(id));
                availableActivitiesMap.delete(id);
                $('#assign-errors').addClass('d-none');
                reloadActivitiesLists();
            } else {
                $('#assign-errors').removeClass('d-none');
                $('#assign-error').text("Nie można przypisać zajęć o id: " + id);
            }
        }, false);
    }
    if (document.querySelector('.to-un-assign') != null) {
        document.querySelector('.to-un-assign').addEventListener('click', function (evt) {
            var id = +evt.target.getAttribute('data-activityid');
            if (assignedActivitiesMap.get(id) !== undefined) {
                availableActivitiesMap.set(id, assignedActivitiesMap.get(id));
                assignedActivitiesMap.delete(id);
                $('#delete-errors').addClass('d-none');
                reloadActivitiesLists();
            } else {
                $('#delete-errors').removeClass('d-none');
                $('#delete-error').text("Nie można wypisać zajęć o id: " + id);
            }
        }, false);
    }

    function reloadActivitiesLists() {
        availableActivities.innerHTML = "";
        assignedActivities.innerHTML = "";
        assignedActivitiesMap = new Map([...assignedActivitiesMap.entries()].sort());
        availableActivitiesMap = new Map([...availableActivitiesMap.entries()].sort());
        Array.from(assignedActivitiesMap.values()).forEach(x => assignedActivities.innerHTML += x.outerHTML + "\n");
        Array.from(availableActivitiesMap.values()).forEach(x => availableActivities.innerHTML += x.outerHTML + "\n");
    }

    function handleSaveButton() {
        $('#errors').addClass("d-none");
        if (checkActivityInputs()) {
            var trimedValue = (JSON.parse(JSON.stringify(nameInput.value))).trim();
            nameInput.value = trimedValue;
            $.ajax({
                type: 'POST',
                url: '/admin/plan?' + $.param({
                    "name": trimedValue,
                    "assignedactivities": Array.from(assignedActivitiesMap.keys()).join(',')
                })
            }).done(function () {
                window.location.href = "/admin/plans";
            }).fail(function (msg) {
                $('#errors').removeClass("d-none");
                $('#type-error').text("Nie można doadać tego planu");
            })
        }
    }

    btnSave.addEventListener('click', function () {
        handleSaveButton();
    }, false);
})();