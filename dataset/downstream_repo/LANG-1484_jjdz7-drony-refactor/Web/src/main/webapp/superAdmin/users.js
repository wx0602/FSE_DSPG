// (function () {
var selects = document.querySelectorAll('#userType');
for (let i = 0; i < selects.length; i++) {
    selects[i].addEventListener('change', function (e) {
        $.ajax({
            type: 'PUT',
            url: '/admin/users?' + $.param({
                "id": e.target.getAttribute('data-userId'),
                "select": e.target.value
            })
        })
    }, false);
}


// })();