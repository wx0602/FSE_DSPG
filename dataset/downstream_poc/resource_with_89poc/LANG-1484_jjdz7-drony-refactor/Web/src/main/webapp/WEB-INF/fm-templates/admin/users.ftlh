<#import "../parts/macros/basic.ftlh" as basic/>
<@basic.includeContent scriptsSrc="" currentPosition="users" modal=""permissionLevel="ADMIN">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5 mb-5">
            <h2>Użytkownicy</h2>
            <#list users>
                <ul class="list-group w-100 ">
                    <#items as user>
                        <li class="list-group-item" href="/user?id=${user.id}" class="stretched-link">
                            email: ${user.email}, imię: ${user.name}, nazwisko: ${user.surname}
                        </li>
                    </#items>
                </ul>
            </#list>
            <#if users?size == 0>
                <p>Nie ma obecnie żadnych użytkowników</p>
            </#if>
        </div>
    </div>
</@basic.includeContent>