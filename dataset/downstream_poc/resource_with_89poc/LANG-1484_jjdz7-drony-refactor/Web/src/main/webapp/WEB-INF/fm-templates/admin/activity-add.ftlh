<#import "../parts/macros/basic.ftlh" as baisc/>
<@baisc.includeContent scriptsSrc="activity-add.js" currentPosition="none" modal="" permissionLevel="ADMIN">
    <div class="row">
        <div class="col-10 ml-auto mr-auto mt-5">
            <h2>Zajęcia</h2>
            <form>
                <div class="form-group row">
                    <label for="name" class="col-sm-2 col-form-label">Nazwa</label>
                    <div class="col-sm-10">
                        <input type="text" class="form-control name" id="name" placeholder="Nazwa zajęć">
                    </div>
                </div>
                <div class="form-group row">
                    <label for="maxUsers" class="col-sm-6 col-lg-3 col-form-label maxUsersLabel">Max l. użytkowników: x</label>
                    <div class="col-sm-6 col-lg-3 mr-auto">
                        <input type="number" class="custom-range maxUsers" value="1" min="1">
                    </div>
                </div>
                <div class="form-group row">
                    <label for="duration" class="col-sm-6 col-lg-3 col-form-label durationLabel">Czas trwania: x</label>
                    <div class="col-sm-6 col-lg-3 mr-auto">
                        <input type="number" class="custom-range duration" min="1" value="1" id="duration">
                    </div>
                </div>
                <div class="form-group">
                    <label for="activityType">Wybierz rodzaj zajęć</label>
                    <select class="form-control" id="activityType">
                        <option value="1">Wykład</option>
                        <option value="2">Ćwiczenia</option>
                        <option value="3">Warsztaty</option>
                    </select>
                </div>
            </form>
            <ul class="list-group w-80 mb-3 border border-danger d-none errors" id="errors">
                <li class="list-group-item type-error" id="type-error"></li>
            </ul>
        </div>
    </div>

    <div class="row mt-3">
        <div class="col-3 mb-3 ml-auto mr-auto">
            <button class="btn btn-success text-white w-100 save">Dodaj zajęcia</button>
        </div>
    </div>
</@baisc.includeContent>