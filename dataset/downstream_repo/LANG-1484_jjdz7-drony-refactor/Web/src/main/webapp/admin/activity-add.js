(function () {
    var maxUsersInput = document.querySelector('.maxUsers'),
        nameInput = document.querySelector('.name'),
        maxUsersLabel = document.querySelector('.maxUsersLabel'),
        durationLabel = document.querySelector('.durationLabel'),
        durationInput = document.querySelector('.duration'),
        btnChange = document.querySelector('button.save'),
        errors = document.querySelector('#errors'),
        errorType = document.querySelector('#type-error'),
        activityType = document.querySelector('#activityType');

    setInput(maxUsersLabel, "Max l. użytkowników: ", maxUsersInput.value, "");
    setInput(durationLabel, "Czas trwania: ", durationInput.value * 15, " min");

    function setInput(label, text, value, text2) {
        label.innerText = text + value + text2;
    }

    maxUsersInput.addEventListener('input', function () {
        setInput(maxUsersLabel, "Max l. użytkowników: ", this.value, "")
    }, false);

    durationInput.addEventListener('input', function () {
        setInput(durationLabel, "Czas trwania: ", this.value * 15, " min")
    }, false);

    function checkActivityInputs() {
        if (nameInput.value.trim() == "") {
            $('#errors').removeClass("d-none");
            $('#type-error').text("Pole nazwa jest puste");
            return false;
        }
        return true;
    }

    function handleChangeButton() {
        $('#errors').addClass("d-none");
        if (checkActivityInputs()) {
            var trimedValue = (JSON.parse(JSON.stringify(nameInput.value))).trim();
            nameInput.value = trimedValue;
            $.ajax({
                type: 'POST',
                url: '/admin/activity?' + $.param({
                    "name": trimedValue,
                    "maxusers": maxUsersInput.value,
                    "duration": durationInput.value,
                    "activitytype": activityType.value
                })
            }).done(function () {
                window.location.href = "/admin/activities";
            }).fail(function (msg) {
                $('#errors').removeClass("d-none");
                $('#type-error').text("Nie można doadać tych zajęć");
            })
        }
    }

    btnChange.addEventListener('click', function () {
        handleChangeButton();
    }, false);
})();
