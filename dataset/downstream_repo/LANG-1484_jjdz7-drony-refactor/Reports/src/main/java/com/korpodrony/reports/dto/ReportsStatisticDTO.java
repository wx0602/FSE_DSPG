package com.korpodrony.reports.dto;

import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;

import javax.validation.constraints.NotNull;
import java.io.Serializable;
import java.time.LocalDateTime;

public class ReportsStatisticDTO implements Serializable {

    private static final long serialVersionUID = 42L;

    private int id;
    @NotNull
    private String email;
    @NotNull
    private View view;
    @NotNull
    private Action action;

    private String timeOfAction;

    public ReportsStatisticDTO(int id, String email, View view, Action action, LocalDateTime timeOfAction) {
        this.id = id;
        this.email = email;
        this.view = view;
        this.action = action;
        this.timeOfAction = LocalDateTimeConverter.fromLocalDateTime(timeOfAction);
    }

    public ReportsStatisticDTO() {
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public View getView() {
        return view;
    }

    public void setView(View view) {
        this.view = view;
    }

    public Action getAction() {
        return action;
    }

    public void setAction(Action action) {
        this.action = action;
    }

    public String getTimeOfAction() {
        return timeOfAction;
    }

    public void setTimeOfAction(String timeOfAction) {
        this.timeOfAction = timeOfAction;
    }
}
