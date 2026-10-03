<#import "../parts/macros/basic.ftlh" as baisc/>
<@baisc.includeContent scriptsSrc="plan-add.js" currentPosition="none" modal="" permissionLevel="ADMIN">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Plany</h2>
            <form>
                <div class="form-group row">
                    <label for="name" class="col-sm-2 col-form-label">Nazwa</label>
                    <div class="col-sm-10">
                        <input type="text" class="form-control name" id="name" placeholder="Nazwa planu">
                    </div>
                </div>
            </form>
            <ul class="list-group w-80 mb-3 border border-danger d-none errors" id="errors">
                <li class="list-group-item type-error" id="type-error"></li>
            </ul>
        </div>
    </div>
    <div class="row mt-3">
        <div class="col-3 mb-3 ml-auto mr-auto">
            <button class="btn btn-success text-white w-100 save">Dodaj plan</button>
        </div>
    </div>

    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Zajęcia przypisane do planu</h2>
            <input type="text" class="form-control" placeholder="Wpisz nazwę zajęć"
                   aria-label="deleteUser" aria-describedby="basic-addon2" id="unAssignInput">
            <ul class="list-group limited-height mb-3 to-un-assign" id="assignedActivities">
            </ul>
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
            <h2>Zajęcia, które można przypisać do planu</h2>
            <input type="text" class="form-control" placeholder="Wpisz nazwę zajęć"
                   aria-label="assignUser" aria-describedby="basic-addon2" id="assignInput">
            <#list activities>
                <ul class="list-group limited-height mb-3 to-assign" id="availableActivities">
                    <#items as activity>
                        <li class="list-group-item" data-activityid="${activity.id}" data-name="${activity.name}">
                            nazwa: ${activity.name} - ${activity.activitiesType.polishName}</li>
                    </#items>
                </ul>
            </#list>
            <#if activities?size ==0>
                <p>Nie ma obecnie żadnych zajęć, których można zapisać do planu</p>
            </#if>
        </div>
    </div>
</@baisc.includeContent>