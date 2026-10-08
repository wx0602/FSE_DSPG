package com.korpodrony.services;

import javax.enterprise.context.SessionScoped;
import java.io.Serializable;

@SessionScoped
public class CurrentUserService implements Serializable {


    String email;

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
