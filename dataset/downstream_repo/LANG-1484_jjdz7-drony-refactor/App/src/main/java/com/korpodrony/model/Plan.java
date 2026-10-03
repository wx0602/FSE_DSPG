package com.korpodrony.model;

import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public class Plan {
    private static int currentID = 0;

    private int id;
    private String name;
    private Set<Integer> activitiesID;

    public Plan(int id, String name, Set<Integer> activitiesID) {
        this.id = id;
        this.name = name;
        this.activitiesID = activitiesID;
    }

    public Plan() {
    }
    public static void setCurrentID(Set<Plan> plans){
        int maxValue = 0;
        for (Plan plan: plans){
            if (plan.getId()>maxValue){
                maxValue=plan.getId();
            }
        }
        setCurrentID(maxValue);
    }

    public static int getCurrentID() {
        return currentID;
    }

    public static void setCurrentID(int currentID) {
        Plan.currentID = currentID;
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

    public Set<Integer> getActivitiesID() {
        return activitiesID;
    }

    public void setActivitiesID(Set<Integer> activitiesID) {
        this.activitiesID = activitiesID;
    }

    public Plan(String name) {
        this(++currentID, name, new HashSet<>());
    }

    public void editPlan(String name) {
        setName(name);
    }

    public boolean assignActivity(Activity activity) {
        if (activitiesID.contains(activity.getId())) {
            return false;
        }
        activitiesID.add(activity.getId());
        return true;
    }

    public boolean assignActivity(int index) {
        if (activitiesID.contains(index)) {
            return false;
        }
        activitiesID.add(index);
        return true;
    }

    public boolean unassignActivity(int index) {
        if (!activitiesID.contains(index)) {
            return false;
        }
        activitiesID.remove(index);
        return true;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Plan plan = (Plan) o;
        return id == plan.id;
    }

    @Override
    public String toString() {
        return "Plan: "+"id = " + id +
                ", nazwa planu:  " + name +
                ", id przypisanych zajęć: " + activitiesID;
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}