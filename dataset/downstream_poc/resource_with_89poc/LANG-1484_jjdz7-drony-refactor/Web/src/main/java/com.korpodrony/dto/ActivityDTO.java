package com.korpodrony.dto;

import com.korpodrony.model.ActivitiesType;

import java.util.List;

public class ActivityDTO {
    private int id;
    private String name;
    private short maxUsers;
    private List<UserDTO> assignedUsers;
    private byte lengthInQuarters;
    private ActivitiesType activitiesType;

    public ActivityDTO(int id, String name, short maxUsers, List<UserDTO> assignedUsers, byte lengthInQuarters, ActivitiesType activitiesType) {
        this.id = id;
        this.name = name;
        this.maxUsers = maxUsers;
        this.assignedUsers = assignedUsers;
        this.lengthInQuarters = lengthInQuarters;
        this.activitiesType = activitiesType;
    }

    public ActivityDTO() {
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

    public short getMaxUsers() {
        return maxUsers;
    }

    public void setMaxUsers(short maxUsers) {
        this.maxUsers = maxUsers;
    }

    public List<UserDTO> getAssignedUsers() {
        return assignedUsers;
    }

    public void setAssignedUsers(List<UserDTO> assignedUsers) {
        this.assignedUsers = assignedUsers;
    }

    public byte getLengthInQuarters() {
        return lengthInQuarters;
    }

    public void setLengthInQuarters(byte lengthInQuarters) {
        this.lengthInQuarters = lengthInQuarters;
    }

    public ActivitiesType getActivitiesType() {
        return activitiesType;
    }

    public void setActivitiesType(ActivitiesType activitiesType) {
        this.activitiesType = activitiesType;
    }
}
