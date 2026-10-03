<#import "../parts/macros/basic.ftlh" as baisc/>
<@baisc.includeContent scriptsSrc="" currentPosition="plans" modal="" permissionLevel="ADMIN">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Plany</h2>
            <#list plans>
                <ul class="list-group w-100 ">
                    <#items as plan>
                        <li class="list-group-item"><a href="/admin/plan?id=${plan.id}" class="stretched-link">
                                nazwa: ${plan.name}</a></li>
                    </#items>
                </ul>
            </#list>
            <#if plans?size == 0>
                <p>Nie ma obecnie żadnych planów</p>
            </#if>
        </div>
    </div>
    <div class="row mt-3">
        <div class="col-3 ml-auto mr-auto mb-3">
            <a class="btn btn-success text-white w-100" href="/admin/plan-add">Dodaj</a>
        </div>
    </div>
</@baisc.includeContent>