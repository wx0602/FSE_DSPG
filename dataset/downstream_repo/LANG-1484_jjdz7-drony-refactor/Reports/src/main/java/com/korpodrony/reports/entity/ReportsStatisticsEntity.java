package com.korpodrony.reports.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity(name = "ReportsStatistics")
@Table(name = "reportsStatistics")
public class ReportsStatisticsEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int id;

    private String email;
    private View view;
    private Action action;
    private LocalDateTime timeOfAction;

    public ReportsStatisticsEntity(String email, View view, Action action, LocalDateTime timeOfAction) {
        this.email = email;
        this.view = view;
        this.action = action;
        this.timeOfAction = timeOfAction;
    }

    public ReportsStatisticsEntity() {
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

    public void setEmail(String userId) {
        this.email = userId;
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

    public LocalDateTime getTimeOfAction() {
        return timeOfAction;
    }

    public void setTimeOfAction(LocalDateTime timeOfAction) {
        this.timeOfAction = timeOfAction;
    }

    @Override
    public String toString() {
        return "ReportsStatisticsEntity{" +
                "id=" + id +
                ", email=" + email +
                ", view=" + view +
                ", action=" + action +
                ", timeOfAction=" + timeOfAction +
                '}';
    }
}
