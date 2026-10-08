(function () {
    var btnSearchUsers = document.querySelector('#btnSearchUser'),
        btnSearchActivities = document.querySelector('#btnSearchActivities'),
        btnSearchPlans = document.querySelector('#btnSearchPlans'),
        searchInput = document.querySelector('#searchInput'),
        results = document.querySelector('#results'),
        URL = "/admin/search-activity",
        response;

    function setURL(txt) {
        removePressedStatus();
        results.innerHTML = "";
        searchInput.value = "";
        searchInput.focus();
        URL = txt;
    }

    function removePressedStatus() {
        btnSearchUsers.classList.remove('btn-success');
        btnSearchUsers.classList.add('btn-secondary');
        btnSearchActivities.classList.remove('btn-success');
        btnSearchActivities.classList.add('btn-secondary');
        btnSearchPlans.classList.remove('btn-success');
        btnSearchPlans.classList.add('btn-secondary');
    }

    btnSearchUsers.addEventListener('click', function () {
        setURL("/admin/search-users");
        btnSearchUsers.classList.remove('btn-secondary');
        btnSearchUsers.classList.add('btn-success');
    }, false);

    btnSearchActivities.addEventListener('click', function () {
        setURL("/admin/search-activities");
        btnSearchActivities.classList.remove('btn-secondary');
        btnSearchActivities.classList.add('btn-success');
    }, false);

    btnSearchPlans.addEventListener('click', function () {
        setURL("/admin/search-plans");
        btnSearchPlans.classList.remove('btn-secondary');
        btnSearchPlans.classList.add('btn-success');
    }, false);

    btnSearchUsers.click();

    function handleInput() {
        $.ajax({
            type: 'GET',
            url: URL + "?" + $.param({
                "name": searchInput.value
            })
        }).done(function (resp) {
            response = resp;
            if (resp.length > 0) {
                results.innerHTML = prepareList(resp);
            } else {
                results.innerHTML = badRequest();
            }
        }).fail(function (msg) {
            results.innerHTML = badRequest();
        })
    }

    function prepareList(resp) {
        if (URL == "/admin/search-users") {
            return prepareUsersList(resp);
        } else if (URL == "/admin/search-activities") {
            return prepareActivitiesList(resp);
        } else if (URL == "/admin/search-plans") {
            return preparePlansList(resp);
        }
    }

    function prepareUsersList(resp) {
        var str = "";
        for (var i = 0; i < resp.length; i++) {
            str += prepareUser(resp[i]);
        }
        return str;
    }

    function prepareUser(user) {
        return "<li class=\"list-group-item\">email: " + user.email +
            ", imię: " + user.name + ", nazwisko: " + user.surname + "</li> "
    }

    function prepareActivitiesList(resp) {
        var str = "";
        for (var i = 0; i < resp.length; i++) {
            var activity = polishActivity(resp[i]);
            str += prepareActivity(activity);
        }
        return str;
    }

    function polishActivity(element) {
        if (element.activitiesType == "LECTURE") {
            element.activitiesType = "wykład"
        } else if (element.activitiesType == "EXERCISE") {
            element.activitiesType = "ćwiczenia"
        } else if (element.activitiesType == "WORKSHOP") {
            element.activitiesType = "warsztaty"
        }
        return element;
    }

    function prepareActivity(activity) {
        return "<li class=\"list-group-item\"><a href=\"/activity?id=" + activity.id + "\" class=\"stretched-link\"> nazwa: "
            + activity.name + " - " + activity.activitiesType + "</a></li> ";
    }

    function badRequest() {
        return "<li class=\"list-group-item\"> Nie znaleziono wyników dla podanego hasła</li> "
    }

    function preparePlan(plan) {
        return "<li class=\"list-group-item\"><a href=\"/plan?id=" + plan.id + "\" class=\"stretched-link\"> nazwa: "
            + plan.name + "</a></li> ";
    }

    function preparePlansList(resp) {
        var str = "";
        for (var i = 0; i < resp.length; i++) {
            str += preparePlan(resp[i]);
        }
        return str;
    }

    searchInput.addEventListener("keyup", function (evt) {
        if (searchInput.value.length > 0) {
            handleInput();
        } else {
            results.innerHTML = "";
        }
    }, false);
})();