<#import "../parts/macros/basic.ftlh" as basic/>
<@basic.includeContent scriptsSrc="" currentPosition="upload" modal="" permissionLevel="ADMIN">
    <div class="row">
        <span class="warning-message">${message}</span><br/><br/>
        <#if isPrintForm == true>
            <form action="/admin/upload-file" class="py-4" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="fileInput">Wybierz plik z danymi do załadowania (Activities.json, Plans.json lub Users.json):</label>
                    <input name="file" type="file" accept="application/json" class="form-control-file border border-secondary rounded" id="fileInput">
                </div>
                <button type="submit" class="btn btn-primary">Załaduj</button>
            </form>
        </#if>
    </div>
</@basic.includeContent>