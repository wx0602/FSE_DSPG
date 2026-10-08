(function () {
    var activityType = document.querySelector('#activityType');

    $('#activityType').val($('#activityType').attr('data-activitySelect'));

    function handleSelectChange() {
        window.location.href = "/user/activities?type=" + activityType.value;
    }

    activityType.addEventListener('change', handleSelectChange, false);
})();