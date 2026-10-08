package com.korpodrony.model;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public class Activity {
    private static int currentID = 0;
    private int id;
    private String name;
    private short maxUsers;
    private Set<Integer> assignedUsersIDs;
    private Set<User> assignedUsers;
    private byte lengthInQuarters;

    public void setAssignedUsers(Set<User> assignedUsers) {
        this.assignedUsers = assignedUsers;
    }

    private ActivitiesType activitiesType;

    public Activity(String name, short maxUsers, byte lengthInQuarters, ActivitiesType activitiesType) {
        this(++currentID, name, maxUsers, new HashSet<>(), lengthInQuarters, activitiesType);
    }

    public Activity(int id, String name, short maxUsers, Set<Integer> assignedUsersIDs, byte lengthInQuarters, ActivitiesType activitiesType) {
        this.id = id;
        this.name = name;
        this.maxUsers = maxUsers;
        this.assignedUsersIDs = assignedUsersIDs;
        this.lengthInQuarters = lengthInQuarters;
        this.activitiesType = activitiesType;
    }

    public Activity() {
    }

    public static int getCurrentID() {
        return currentID;
    }

    public static void setCurrentID(Set<Activity> activities) {
        int maxValue = 0;
        for (Activity activity : activities) {
            if (activity.getId() > maxValue) {
                maxValue = activity.getId();
            }
        }
        setCurrentID(maxValue);
    }

    public static void setCurrentID(int currentID) {
        Activity.currentID = currentID;
    }

    public Set<User> getAssignedUsers() {
        return assignedUsers;
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

    public Set<Integer> getAssignedUsersIDs() {
        return assignedUsersIDs;
    }

    public void setAssignedUsersIDs(Set<Integer> assignedUsersIDs) {
        this.assignedUsersIDs = assignedUsersIDs;
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

    public void editActivity(String name, short maxUsers, byte lenghtInQuarters, ActivitiesType activitiesType) {
        setName(name);
        setMaxUsers(maxUsers);
        setLengthInQuarters(lenghtInQuarters);
        setActivitiesType(activitiesType);
    }

    public boolean assignUser(int userID) {
        if (canAssignUser(userID)) {
            assignedUsersIDs.add(userID);
            return true;
        }
        return false;
    }

    public boolean assignUser(User user) {
        return assignUser(user.getId());
    }

    public boolean unassignUser(int userID) {
        if (!assignedUsersIDs.contains(userID)) {
            return false;
        }
        assignedUsersIDs.remove(userID);
        return true;
    }

    public boolean unassignUser(User user) {
        return unassignUser(user.getId());
    }

    public boolean canAssignUser(int userID) {
        if (assignedUsersIDs.contains(userID) || assignedUsersIDs.size() == maxUsers) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "Zajęcia: " + "id = " + id +
                ", nazwa: " + name +
                ", maksymalna liczba użytkowników: " + maxUsers +
                ", ID przypisanych użytkowników: " + assignedUsersIDs +
                ", czas trwania [min]:" + lengthInQuarters * 15 +
                ", typ zajęć: " + activitiesType.polishName;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Activity activity = (Activity) o;
        return id == activity.id &&
                maxUsers == activity.maxUsers &&
                lengthInQuarters == activity.lengthInQuarters &&
                Objects.equals(name, activity.name) &&
                Objects.equals(assignedUsersIDs, activity.assignedUsersIDs) &&
                activitiesType == activity.activitiesType;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name, maxUsers, assignedUsersIDs, lengthInQuarters, activitiesType);
    }
}