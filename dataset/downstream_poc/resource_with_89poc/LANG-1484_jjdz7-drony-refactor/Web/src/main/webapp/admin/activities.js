(function () {
    var activityType = document.querySelector('#activityType');

    $('#activityType').val($('#activityType').attr('data-activitySelect'));

    function handleSelectChange() {
        window.location.href = "/admin/activities?type=" + activityType.value;
    }

    activityType.addEventListener('change', handleSelectChange, false);
})();