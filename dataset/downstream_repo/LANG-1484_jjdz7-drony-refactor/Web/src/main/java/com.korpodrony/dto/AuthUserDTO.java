package com.korpodrony.dto;

import com.korpodrony.entity.PermissionLevel;

public class AuthUserDTO {
    private int id;
    private PermissionLevel permissionLevel;

    public AuthUserDTO(int id, PermissionLevel permissionLevel) {
        this.id = id;
        this.permissionLevel = permissionLevel;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public PermissionLevel getPermissionLevel() {
        return permissionLevel;
    }

    public void setPermissionLevel(PermissionLevel permissionLevel) {
        this.permissionLevel = permissionLevel;
    }
}
