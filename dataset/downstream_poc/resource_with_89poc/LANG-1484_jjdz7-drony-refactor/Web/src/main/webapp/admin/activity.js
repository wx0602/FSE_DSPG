(function () {
    var maxUsersInput = document.querySelector('.maxUsers'),
        nameInput = document.querySelector('.name'),
        maxUsersLabel = document.querySelector('.maxUsersLabel'),
        durationLabel = document.querySelector('.durationLabel'),
        durationInput = document.querySelector('.duration'),
        btnChange = document.querySelector('button.change'),
        btnDelete = document.querySelector('button.delete'),
        errors = document.querySelector('#errors'),
        errorType = document.querySelector('#type-error'),
        assingInput = document.querySelector('#assignUserInput'),
        deleteUserInput = document.querySelector('#deleteUserInput'),
        assingUserButton = document.querySelector('#assignUser'),
        deleteUserButton = document.querySelector('#deleteUser'),
        dataId = document.querySelector('[data-id]').getAttribute('data-id'),
        activityType = document.querySelector('#activityType'),
        basicActitiyTypeValue = $('#activityType').attr('data-activitySelect'),
        maxUsersValue = JSON.parse(JSON.stringify(maxUsersInput.value)),
        durationValue = JSON.parse(JSON.stringify(durationInput.value)),
        nameValue = JSON.parse(JSON.stringify(nameInput.value)),
        userIdsToAssign = [],
        userIdsToUnAssign = [];

    $('#activityType').val($('#activityType').attr('data-activitySelect'));

    function setInput(label, text, value, text2) {
        label.innerText = text + value + text2;
    }

    assingInput.addEventListener("keyup", function (e) {
        let value = assingInput.value.toLowerCase();
        document.querySelectorAll('.user-to-assign').forEach(x => x.classList.remove("d-none"));
        if (value === "") {
            return;
        }
        document.querySelectorAll('.user-to-assign').forEach(x => {
            if (!x.getAttribute("data-email").toLowerCase().includes(value)) {
                x.classList.add("d-none");
            }
        });
    }, false);

    deleteUserInput.addEventListener("keyup", function (e) {
        let value = deleteUserInput.value.toLowerCase();
        document.querySelectorAll('.user-to-un-assign').forEach(x => x.classList.remove("d-none"));
        if (value === "") {
            return;
        }
        document.querySelectorAll('.user-to-un-assign').forEach(x => {
            if (!x.getAttribute("data-email").toLowerCase().includes(value)) {
                x.classList.add("d-none");
            }
        });
    }, false);

    if (document.querySelector('.to-assign') !== null) {
        document.querySelector('.to-assign').addEventListener('click', function (e) {
            var id = e.target.getAttribute('data-userid');
            if (userIdsToAssign.includes(id)) {
                $(e.target).removeClass("bg-primary");
                var index = userIdsToAssign.indexOf(id);
                if (index !== -1) userIdsToAssign.splice(index, 1);
                if (userIdsToAssign.length == 0) {
                    $('#assignUser').prop("disabled", true);
                }
            } else {
                $(e.target).addClass("bg-primary");
                userIdsToAssign.push(id);
                $('#assignUser').prop("disabled", false);
                ;
            }
        }, false);
    }
    if (document.querySelector('.to-un-assign') !== null) {
        document.querySelector('.to-un-assign').addEventListener('click', function (e) {
            var id = e.target.getAttribute('data-userid');
            if (userIdsToUnAssign.includes(id)) {
                $(e.target).removeClass("bg-danger");
                var index = userIdsToUnAssign.indexOf(id);
                if (index !== -1) userIdsToUnAssign.splice(index, 1);
                if (userIdsToUnAssign.length == 0) {
                    $('#deleteUser').prop("disabled", true);
                }
            } else {
                $(e.target).addClass("bg-danger");
                userIdsToUnAssign.push(id);
                $('#deleteUser').prop("disabled", false);
            }
        }, false)
    }

    setInput(maxUsersLabel, "Max l. użytkowników: ", maxUsersInput.value, "");
    setInput(durationLabel, "Czas trwania: ", durationInput.value * 15, " min");

    maxUsersInput.addEventListener('input', function () {
        setInput(maxUsersLabel, "Max l. użytkowników: ", this.value, "")
    }, false);

    durationInput.addEventListener('input', function () {
        setInput(durationLabel, "Czas trwania: ", this.value * 15, " min")
    }, false);

    function checkChanges() {
        if (nameInput.value == nameValue
            && maxUsersInput.value == maxUsersValue
            && durationInput.value == durationValue
            && activityType.value == basicActitiyTypeValue) {
            return false;
        } else {
            return true;
        }
    }

    function checkActivityInputs() {
        if (nameInput.value.trim() == "") {
            $('#errors').removeClass("d-none");
            $('#type-error').text("Pole nazwa jest puste");
            return false;
        } else if (!checkChanges()) {
            $('#errors').removeClass("d-none");
            $('#type-error').text("Nic nie zmieniono");
            return false
        }
        return true;
    }

    function handleChangeButton() {
        $('#errors').addClass("d-none");
        if (checkActivityInputs()) {
            var trimedValue = (JSON.parse(JSON.stringify(nameInput.value))).trim();
            nameInput.value = trimedValue;
            $.ajax({
                type: 'PUT',
                url: '/admin/activity?' + $.param({
                    "id": dataId,
                    "name": trimedValue,
                    "maxusers": maxUsersInput.value,
                    "duration": durationInput.value,
                    "activitytype": activityType.value
                })
            }).done(function () {
                window.location.href = "/admin/activity?id=" + dataId;
            }).fail(function (msg) {
                $('#errors').removeClass("d-none");
                $('#type-error').text("Nie można zmienic danych zajęć o id: " + dataId);
            })
        }
    }

    btnChange.addEventListener('click', function () {
        handleChangeButton();
    }, false);

    assingUserButton.addEventListener('click', function () {
        handleAddButton();
    }, false);

    $('#delete-activty').click(function () {
        $.ajax({
            type: 'DELETE',
            url: '/admin/activity?' + $.param({
                "id": dataId,
            })
        }).done(function () {
            window.location.href = "/admin/activities";
        }).fail(function (msg) {
            $('#errors').removeClass("d-none");
            $('#type-error').text("Nie można usunąć zajęć o id: " + dataId);
        })
    })

    function handleAddButton() {
        $('#assign-errors').addClass('d-none');
        $.ajax({
            type: 'PUT',
            url: '/admin/activity-assign?' + $.param({
                "id": dataId,
                "userid": userIdsToAssign.join(",")
            })
        }).done(function () {
            window.location.href = "/admin/activity?id=" + dataId;
        }).fail(function (msg) {
            $('#assign-errors').removeClass('d-none');
            $('#assign-error').text("Nie można dodać użytkowników");
        })
    }

    deleteUserButton.addEventListener('click', function () {
        handleDeleteButton();
    }, false);

    function handleDeleteButton() {
        $('#delete-errors').addClass('d-none');
        $.ajax({
            type: 'PUT',
            url: '/admin/activity-unassign?' + $.param({
                "id": dataId,
                "userid": userIdsToUnAssign.join(",")
            })
        }).done(function () {
            window.location.href = "/admin/activity?id=" + dataId;
        }).fail(function (msg) {
            $('#delete-errors').removeClass('d-none');
            $('#delete-error').text("Nie można wypisać użytkowników");
        })
    }
})();