package com.korpodrony.model;

import javax.persistence.*;
import java.util.*;

public class Organization {
    private int id;

    private Set<User> users;
    private Set<Plan> plans;
    private Set<Activity> activities;

    public Organization(Set<User> users, Set<Plan> plans, Set<Activity> activities) {
        this.users = users;
        this.plans = plans;
        this.activities = activities;
    }

    public Organization() {
        this(new HashSet<>(), new HashSet<>(), new HashSet<>());
    }

    public Set<User> getUsers() {
        return users;
    }

    public void setUsers(Set<User> users) {
        this.users = users;
    }

    public Set<Plan> getPlans() {
        return plans;
    }

    public void setPlans(Set<Plan> plans) {
        this.plans = plans;
    }

    public Set<Activity> getActivities() {
        return activities;
    }

    public void setActivities(Set<Activity> activities) {
        this.activities = activities;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Organization that = (Organization) o;
        return Objects.equals(users, that.users) &&
                Objects.equals(plans, that.plans) &&
                Objects.equals(activities, that.activities);
    }

    @Override
    public int hashCode() {
        return Objects.hash(users, plans, activities);
    }
}