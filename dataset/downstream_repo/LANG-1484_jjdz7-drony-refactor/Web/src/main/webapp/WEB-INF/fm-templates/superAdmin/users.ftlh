<#import "../parts/macros/basic.ftlh" as basic/>
<@basic.includeContent scriptsSrc="../superAdmin/users.js" currentPosition="users" modal=""permissionLevel="ADMIN">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5 mb-5">
            <h2>Użytkownicy</h2>
            <#list users>
                <ul class="list-group w-100 ">
                    <#items as user>
                        <li class="list-group-item" href="/user?id=${user.id}" class="stretched-link">
                            <div class="row">
                                <div class="col-8">
                                    email: ${user.email}, imię: ${user.name}, nazwisko: ${user.surname}
                                </div>
                                <div class="col-4">
                                    <select class="custom-select" data-userId="${user.id}" id="userType"
                                            value="${user.permissionLevel}">
                                        <#if user.permissionLevel == "SUPER_ADMIN">
                                            <option value="SUPER_ADMIN" selected>SUPER ADMIN</option>
                                            <option value="ADMIN">ADMIN</option>
                                            <option value="USER">USER</option>
                                        <#elseif user.permissionLevel == "ADMIN">
                                            <option value="SUPER_ADMIN">SUPER ADMIN</option>
                                            <option value="ADMIN" selected>ADMIN</option>
                                            <option value="USER">USER</option>
                                        <#else>
                                            <option value="SUPER_ADMIN">SUPER ADMIN</option>
                                            <option value="ADMIN">ADMIN</option>
                                            <option value="USER" selected>USER</option>
                                        </#if>
                                    </select>
                                </div>
                            </div>
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