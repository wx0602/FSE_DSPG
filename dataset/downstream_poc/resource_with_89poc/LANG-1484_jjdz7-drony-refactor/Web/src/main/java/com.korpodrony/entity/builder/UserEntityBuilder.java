package com.korpodrony.entity.builder;

import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.entity.UserEntity;

public final class UserEntityBuilder {
    private String name;
    private String surname;
    private String email;
    private PermissionLevel permissionLevel = PermissionLevel.USER;

    private UserEntityBuilder() {
    }

    public static UserEntityBuilder anUserEntity() {
        return new UserEntityBuilder();
    }

    public UserEntityBuilder withName(String name) {
        this.name = name;
        return this;
    }

    public UserEntityBuilder withSurname(String surname) {
        this.surname = surname;
        return this;
    }

    public UserEntityBuilder withEmail(String email) {
        this.email = email;
        return this;
    }

    public UserEntityBuilder withPermissionLevel(PermissionLevel permissionLevel) {
        this.permissionLevel = permissionLevel;
        return this;
    }

    public UserEntity build() {
        UserEntity userEntity = new UserEntity();
        userEntity.setName(name);
        userEntity.setSurname(surname);
        userEntity.setEmail(email);
        userEntity.setPermissionLevel(permissionLevel);
        return userEntity;
    }
}
