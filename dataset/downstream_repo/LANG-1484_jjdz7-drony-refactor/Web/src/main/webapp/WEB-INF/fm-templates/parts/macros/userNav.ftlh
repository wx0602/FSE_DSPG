<#macro setNav current>
    <a class="banner nav-link nav-item" href="/index"> Korpodrony</a>
    <nav class="navbar navbar-expand-lg navbar-light bg-primary">
        <button class="navbar-toggler ml-auto mr-auto" type="button" data-toggle="collapse" data-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse justify-content-center" id="navbarNav">
            <ul class="navbar-nav col-lg-10 col-sm-12">
                <#if current=="activities">
                    <li class="nav-item active">
                        <a class="nav-link text-center">Zajęcia</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/user/activities">Zajęcia</a>
                    </li>
                </#if>
                <#if current=="userActivities">
                    <li class="nav-item active">
                        <a class="nav-link text-center">Moje Zajęcia</a>
                    </li>
                <#else>
                    <li class="nav-item">
                        <a class="nav-link text-white text-center" href="/user/useractivities">Moje Zajęcia</a>
                    </li>
                </#if>
                <li class="nav-item active">
                    <a class="nav-link text-white text-center" href="/logout">Wyloguj</a>
                </li>
            </ul>
        </div>
    </nav>
</#macro>