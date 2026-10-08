<#import "../parts/macros/basic.ftlh" as baisc/>
<@baisc.includeContent scriptsSrc="activities.js" currentPosition="userActivities" modal="" permissionLevel="USER">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5 mb-5">
            <h2>Moje Zajęcia</h2>
            <div class="form-group">
                <label for="activityType">Wybierz rodzaj zajęć</label>
                <select class="form-control" data-activitySelect="${type}"
                        id="activityType">
                    <option value="1">Wykłady</option>
                    <option value="2">Ćwiczenia</option>
                    <option value="3">Warsztaty</option>
                    <option value="4">Wszystkie</option>
                </select>
            </div>
            <#list activities>
                <ul class="list-group w-100 ">
                    <#items as activity>
                        <li class="list-group-item">
                            nazwa: ${activity.name} - ${activity.activitiesType.polishName}</li>
                    </#items>
                </ul>
            </#list>
            <#if activities?size == 0>
                <p>Nie ma obecnie żadnych zajęć podanego typu</p>
            </#if>
        </div>
    </div>
</@baisc.includeContent>