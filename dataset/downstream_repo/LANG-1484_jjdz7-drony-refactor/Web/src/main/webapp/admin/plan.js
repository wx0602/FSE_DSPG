(function () {
    var nameInput = document.querySelector('.name'),
        btnChange = document.querySelector('button.change'),
        btnDelete = document.querySelector('button.delete'),
        errors = document.querySelector('#errors'),
        errorType = document.querySelector('#type-error'),
        assingInput = document.querySelector('#assignInput'),
        unAssignInput = document.querySelector('#unAssignInput'),
        assignButton = document.querySelector('#assignActivity'),
        unAssignButton = document.querySelector('#unassignActivity'),
        dataId = document.querySelector('[data-id]').getAttribute('data-id'),
        nameValue = JSON.parse(JSON.stringify(nameInput.value)),
        idsToAssign = [],
        idsToUnAssign = [];

    assingInput.addEventListener("keyup", function (e) {
        let value = assingInput.value.toLowerCase();
        document.querySelectorAll('.activity-to-assign').forEach(x => x.classList.remove("d-none"));
        if (value === "") {
            return;
        }
        document.querySelectorAll('.activity-to-assign').forEach(x => {
            if (!x.getAttribute("data-name").toLowerCase().includes(value)) {
                x.classList.add("d-none");
            }
        });
    }, false);

    unAssignInput.addEventListener("keyup", function (e) {
        let value = unAssignInput.value.toLowerCase();
        document.querySelectorAll('.activity-to-un-assign').forEach(x => x.classList.remove("d-none"));
        if (value === "") {
            return;
        }
        document.querySelectorAll('.activity-to-un-assign').forEach(x => {
            if (!x.getAttribute("data-name").toLowerCase().includes(value)) {
                x.classList.add("d-none");
            }
        });
    }, false);

    if (document.querySelector('.to-assign') !== null) {
        document.querySelector('.to-assign').addEventListener('click', function (e) {
            var id = e.target.getAttribute('data-activityId');
            if (idsToAssign.includes(id)) {
                $(e.target).removeClass("bg-primary");
                var index = idsToAssign.indexOf(id);
                if (index !== -1) idsToAssign.splice(index, 1);
                if (idsToAssign.length == 0) {
                    $('#assignActivity').prop("disabled", true);
                }
            } else {
                $(e.target).addClass("bg-primary");
                idsToAssign.push(id);
                $('#assignActivity').prop("disabled", false);
                ;
            }
        }, false);
    }
    if (document.querySelector('.to-un-assign') !== null) {
        document.querySelector('.to-un-assign').addEventListener('click', function (e) {
            var id = e.target.getAttribute('data-activityId');
            if (idsToUnAssign.includes(id)) {
                $(e.target).removeClass("bg-danger");
                var index = idsToUnAssign.indexOf(id);
                if (index !== -1) idsToUnAssign.splice(index, 1);
                if (idsToUnAssign.length == 0) {
                    $('#unassignActivity').prop("disabled", true);
                }
            } else {
                $(e.target).addClass("bg-danger");
                idsToUnAssign.push(id);
                $('#unassignActivity').prop("disabled", false);
            }
        }, false)
    }

    function checkChanges() {
        if (nameInput.value == nameValue) {
            return false;
        } else {
            return true;
        }
    }

    function checkPlanInputs() {
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
        if (checkPlanInputs()) {
            var trimedValue = (JSON.parse(JSON.stringify(nameInput.value))).trim();
            nameInput.value = trimedValue;
            $.ajax({
                type: 'PUT',
                url: '/admin/plan?' + $.param({
                    "id": dataId,
                    "name": trimedValue
                })
            }).done(function () {
                window.location.href = "/admin/plan?id=" + dataId;
            }).fail(function (msg) {
                $('#errors').removeClass("d-none");
                $('#type-error').text("Nie można zmienic danych planu o id: " + dataId);
            })
        }
    }

    btnChange.addEventListener('click', function () {
        handleChangeButton();
    }, false);

    assignButton.addEventListener('click', function () {
        handleAddButton();
    }, false);

    $('#delete-plan').click(function () {
        $.ajax({
            type: 'DELETE',
            url: '/admin/plan?' + $.param({
                "id": dataId,
            })
        }).done(function () {
            window.location.href = "/admin/plans";
        }).fail(function (msg) {
            $('#errors').removeClass("d-none");
            $('#type-error').text("Nie można usunąć planu o id: " + dataId);
        })
    })

    function handleAddButton() {
        $('#assign-errors').addClass('d-none');
        $.ajax({
            type: 'PUT',
            url: '/admin/plan-assign?' + $.param({
                "id": dataId,
                "activityid": idsToAssign.join(",")
            })
        }).done(function () {
            window.location.href = "/admin/plan?id=" + dataId;
        }).fail(function (msg) {
            $('#assign-errors').removeClass('d-none');
            $('#assign-error').text("Nie można dodać zajęć");
        })
    }

    unAssignButton.addEventListener('click', function () {
        handleDeleteButton();
    }, false);

    function handleDeleteButton() {
        $('#delete-errors').addClass('d-none');
        $.ajax({
            type: 'PUT',
            url: '/admin/plan-unassign?' + $.param({
                "id": dataId,
                "activityid": idsToUnAssign.join(",")
            })
        }).done(function () {
            window.location.href = "/admin/plan?id=" + dataId;
        }).fail(function (msg) {
            $('#delete-errors').removeClass('d-none');
            $('#delete-error').text("Nie można wypisać zajęć");
        })
    }
})();