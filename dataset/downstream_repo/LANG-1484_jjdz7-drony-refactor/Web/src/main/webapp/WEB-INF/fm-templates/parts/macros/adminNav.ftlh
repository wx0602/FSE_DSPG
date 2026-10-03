<#macro setNav current>
    <a class="banner nav-link nav-item" href="/index"> Korpodrony</a>
    <nav class="navbar navbar-expand-lg navbar-light bg-primary">
        <button class="navbar-toggler ml-auto mr-auto" type="button" data-toggle="collapse" data-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse justify-content-center" id="navbarNav">
            <ul class="navbar-nav col-lg-10 col-sm-12">
                <#if current=="users">
                    <li class="nav-item active">
                        <a class="nav-link text-center">Użytkownicy</a>
                    </li>
                <#else>
                    <li class="nav-item active">
                        <a class="nav-link text-white text-center" href="/admin/users">Użytkownicy</a>
                    </li>
                </#if>
                <#if current=="activities">
                    <li class="nav-item active">
                        <a class="nav-link text-center">Zajęcia</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/admin/activities">Zajęcia</a>
                    </li>
                </#if>
                <#if current=="plans">
                    <li class="nav-item active">
                        <a class="nav-link text-center">Plany</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/admin/plans">Plany</a>
                    </li>
                </#if >
                <#if current=="search">
                    <li class="nav-item  active">
                        <a class="nav-link ml-auto text-center">Szukaj</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/admin/search">Szukaj</a>
                    </li>
                </#if>
                <#if current=="upload">
                    <li class="nav-item  active">
                        <a class="nav-link text-center">Wczytaj plik</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/admin/upload-file">Wczytaj plik</a>
                    </li>
                </#if>
                <#if current=="admin-panel">
                    <li class="nav-item  active">
                        <a class="nav-link text-center">Panel Administracyjny</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/admin/admin-panel">Panel Administracyjny</a>
                    </li>
                </#if>
                <li class="nav-item">
                    <a class="nav-link text-white text-center" href="/logout">Wyloguj</a>
                </li>
            </ul>
        </div>
    </nav>
</#macro>