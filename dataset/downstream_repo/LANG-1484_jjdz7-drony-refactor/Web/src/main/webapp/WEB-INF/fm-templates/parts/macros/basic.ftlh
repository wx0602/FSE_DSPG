<#macro includeContent scriptsSrc currentPosition modal permissionLevel>
    <#if permissionLevel=="ADMIN">
        <#assign navBar ="./adminNav.ftlh">
    <#elseif permissionLevel=="USER">
        <#assign navBar = "./userNav.ftlh">
    <#else>
        <#assign navBar = "./guestNav.ftlh">
    </#if>
    <!doctype html>
    <html lang="pl">
    <#include "../header.ftlh">
    <body>
    <#import navBar as nav>
    <@nav.setNav current=currentPosition/>
    <div id="particles-js">
        <div class="container pr-5 pl-5 mt-5 mb-5">
            <#nested>
        </div>
    </div>
    <#if modal !="">
        <#include modal>
    </#if>
    <#import "scripts.ftlh" as scripts>
    <@scripts.setScripts script=scriptsSrc/>
    </body>
    </html>
</#macro>