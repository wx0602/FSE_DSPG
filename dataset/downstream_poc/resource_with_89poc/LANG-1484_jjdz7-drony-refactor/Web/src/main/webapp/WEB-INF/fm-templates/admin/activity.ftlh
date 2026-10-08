<#import "../parts/macros/basic.ftlh" as basic/>
<@basic.includeContent scriptsSrc="activity.js" currentPosition="none" modal="../activity-modal.ftlh" permissionLevel="ADMIN">

    <#if users?size !=0 >
        <#assign minUsers = users?size>
        <#assign maxUsers = 30+users?size>
    <#else>
        <#assign minUsers = 1>
        <#assign maxUsers = 30>
    </#if>

    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Zajęcia</h2>
            <form>
                <div class="form-group row">
                    <label for="id" class="col-sm-2 col-form-label">ID:</label>
                    <div class="col-sm-10">
                        <input type="number" readonly class="form-control-plaintext" id="id" data-id="${activity.id}"
                               value="${activity.id}">
                    </div>
                </div>
                <div class="form-group row">
                    <label for="name" class="col-sm-2 col-form-label">Nazwa</label>
                    <div class="col-sm-10">
                        <input type="text" class="form-control name" id="name" value="${activity.name}"
                               placeholder="${activity.name}">
                    </div>
                </div>
                <div class="form-group row">
                    <label for="maxUsers" class="col-sm-6 col-lg-3 col-form-label maxUsersLabel">Max l. użytkowników: x</label>
                    <div class="col-sm-6 col-lg-3 mr-auto">
                        <input type="number" class="custom-range maxUsers" min="${minUsers}"
                               value="${activity.maxUsers}"
                               id="maxUsers">
                    </div>
                </div>
                <div class="form-group row">
                    <label for="duration" class="col-sm-6 col-lg-3 col-form-label durationLabel">Czas trwania: x</label>
                    <div class="col-sm-6 col-lg-3 mr-auto">
                        <input type="number" class="custom-range duration" min="1"
                               value="${activity.lengthInQuarters}" id="duration">
                    </div>
                </div>
                <div class="form-group">
                    <label for="activityType">Wybierz rodzaj zajęć</label>
                    <select class="form-control" data-activitySelect="${activity.activitiesType.number}"
                            id="activityType">
                        <option value="1">Wykład</option>
                        <option value="2">Ćwiczenia</option>
                        <option value="3">Warsztaty</option>
                    </select>
                </div>
            </form>
            <ul class="list-group w-80 mb-3 border border-danger d-none errors" id="errors">
                <li class="list-group-item type-error" id="type-error"></li>
            </ul>
        </div>
    </div>

    <div class="row mt-3">
        <div class="col-3 mb-3 ml-auto">
            <button class="btn btn-success text-white w-100 change">Zmień</button>
        </div>
        <div class="col-3 mb-3 mr-auto">
            <button class="btn btn-danger text-white w-100 delete" data-toggle="modal"
                    data-target="#exampleModalCenter">usuń
            </button>
        </div>
    </div>

    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5" id="assigned-users">
            <h2>Użytykownicy przypisani do zajęć</h2>
            <input type="text" class="form-control" placeholder="Wpisz email użytkownika"
                   aria-label="deleteUser" aria-describedby="basic-addon2" id="deleteUserInput">
            <#list users>
                <ul class="list-group limited-height mb-3 to-un-assign">
                    <#items as user>
                        <li class="list-group-item user-to-un-assign" data-userid="${user.id}" data-email="${user.email}">email: ${user.email} imię: ${user.name}
                            , nazwisko: ${user.surname}</li>
                    </#items>
                </ul>
            </#list>
            <#if users?size == 0>
                <p>Nie ma obecnie żadnych zapisanych użytkowników</p>
            </#if>
        </div>
    </div>

    <div class="row mt-3">
        <div class="col-3 mb-3 ml-auto">
            <button class="btn w-100 bg-danger" id="deleteUser" disabled>Wypisz użytkowników</button>
        </div>
        <div class="col-3 mb-3 mr-auto">
            <button class="btn w-100 bg-primary" id="assignUser" disabled>Zapisz użytkowników</button>
        </div>
    </div>

    <ul class="list-group w-80 mb-3 border border-danger d-none col-10 mr-auto ml-auto errors" id="delete-errors">
        <li class="list-group-item type-error" id="delete-error"></li>
    </ul>

    <ul class="list-group w-80 mb-3 border border-danger mr-auto ml-auto col-10 d-none errors" id="assign-errors">
        <li class="list-group-item type-error" id="assign-error"></li>
    </ul>

    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Użytkownicy, których można zapisać do zajęć</h2>
            <input type="text" class="form-control" placeholder="Wpisz email użytkownika"
                   aria-label="assignUser" aria-describedby="basic-addon2" id="assignUserInput">
            <div class="panel-body">
                <#list availableUsers>
                    <ul class="list-group limited-height mb-3 to-assign">
                        <#items as user>
                            <li class="list-group-item user-to-assign" data-userid="${user.id}" data-email="${user.email}">email: ${user.email} imię: ${user.name}
                                , nazwisko: ${user.surname}</li>
                        </#items>
                    </ul>
                </#list>
                <#if availableUsers?size ==0>
                    <p>Nie ma obecnie żadnych użytkowników, których można zapisać do zajęć</p>
                </#if>
            </div>
        </div>
    </div>
</@basic.includeContent>
