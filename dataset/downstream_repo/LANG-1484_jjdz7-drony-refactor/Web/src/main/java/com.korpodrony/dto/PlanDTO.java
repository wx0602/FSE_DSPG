package com.korpodrony.dto;

import java.util.List;

public class PlanDTO {
    private int id;
    private String name;
    private List<SimplifiedActivityDTO> assignedActivities;

    public PlanDTO(int id, String name, List<SimplifiedActivityDTO> assignedActivities) {
        this.id = id;
        this.name = name;
        this.assignedActivities = assignedActivities;
    }

    public PlanDTO() {
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public List<SimplifiedActivityDTO> getAssignedActivities() {
        return assignedActivities;
    }

    public void setAssignedActivities(List<SimplifiedActivityDTO> assignedActivities) {
        this.assignedActivities = assignedActivities;
    }
}
