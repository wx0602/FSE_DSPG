<#import "../parts/macros/basic.ftlh" as baisc/>
<@baisc.includeContent scriptsSrc="search.js" currentPosition="search" modal="" permissionLevel="ADMIN">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Szukaj</h2>
            <div class="btn-group" role="group" aria-label="Basic example">
                <button type="button" class="btn btn-secondary" id="btnSearchUser">Użytkownicy</button>
                <button type="button" class="btn btn-secondary" id="btnSearchActivities">Zajęcia</button>
                <button type="button" class="btn btn-secondary" id="btnSearchPlans">Plany</button>
            </div>
        </div>
        <div class="input-group mt-5 mb-3">
            <input type="text" class="form-control" placeholder="Szukana fraza" aria-label="Searched text" aria-describedby="basic-addon2" id="searchInput">
        </div>
    </div>
    <div class="row mt-3">
        <ul class="list-group w-100 mb-3" id="results">
        </ul>
    </div>
</@baisc.includeContent>