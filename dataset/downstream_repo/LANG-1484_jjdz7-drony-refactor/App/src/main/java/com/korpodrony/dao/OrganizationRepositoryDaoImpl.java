package com.korpodrony.dao;

import com.korpodrony.model.*;
import com.korpodrony.repository.OrganizationRepository;

import javax.ejb.Stateless;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Stateless
public class OrganizationRepositoryDaoImpl implements OrganizationRepositoryDao {

    private Organization org = OrganizationRepository.getOrganizationRepository();

    @Override
    public boolean editPlan(int planID, String name) {
        if (!hasPlanWithThisID(planID)) {
            return false;
        }
        getPlan(planID).editPlan(name);
        return true;
    }

    @Override
    public boolean hasPlanWithThisID(int planID) {
        return org.getPlans().stream()
                .anyMatch(x->x.getId()==planID);
    }

    @Override
    public Plan getPlan(int planID) {
        return org.getPlans().stream()
                .filter(x->x.getId() == planID)
                .findFirst()
                .orElse(null);
    }

    @Override
    public boolean editActivity(int activityID, String name, short maxUsers, byte lenghtInQuarters, ActivitiesType activitiesType) {
        if (!hasActivityWithThisID(activityID)) {
            return false;
        }
        getActivity(activityID).editActivity(name, maxUsers, lenghtInQuarters, activitiesType);
        return true;
    }

    @Override
    public boolean hasActivityWithThisID(int activityID) {
        return org.getActivities().stream()
                .anyMatch(x->x.getId() == activityID);
    }

    @Override
    public Activity getActivity(int activityID) {
        return org.getActivities().stream()
                .filter(x->x.getId() == activityID)
                .findFirst()
                .orElse(null);
    }

    @Override
    public boolean editUser(int userID, String name, String surname) {
        if (!hasUserWithThisID(userID)) {
            return false;
        }
        getUser(userID).editUser(name, surname);
        return true;
    }

    @Override
    public boolean hasUserWithThisID(int userID) {
        return org.getUsers().stream()
                .anyMatch(x->x.getId() == userID);
    }

    @Override
    public User getUser(int userID) {
        return org.getUsers()
                .stream()
                .filter(x -> x.getId() == userID)
                .findFirst()
                .orElse(null);
    }

    @Override
    public boolean createPlan(String name) {
        return addPlan(new Plan(name));
    }

    @Override
    public boolean hasPlan(Plan plan) {
        return org.getPlans().stream()
                .anyMatch(x->x.equals(plan));
    }

    @Override
    public boolean createActivity(String name, short maxUsers, byte duration, ActivitiesType activitiesType) {
        return addActivity(new Activity(name, maxUsers, duration, activitiesType));
    }

    @Override
    public boolean hasActivity(Activity activity) {
        return org.getActivities().stream()
                .anyMatch(x->x.equals(activity));
    }

    @Override
    public boolean createUser(String name, String surname) {
        return addUser(new User(name, surname));
    }

    @Override
    public boolean hasUser(User user) {
        return org.getUsers().stream()
                .anyMatch(x -> x.equals(user));
    }

    @Override
    public boolean assignActivityToPlan(int activityID, int planID) {
        if (!hasPlanWithThisID(planID) || !hasActivityWithThisID(activityID)) {
            return false;
        }
        return getPlan(planID)
                .assignActivity(activityID);
    }

    @Override
    public boolean unassignActivityFromPlan(int activityID, int planID) {
        if (!hasPlanWithThisID(planID) || !hasActivityWithThisID(activityID)) {
            return false;
        }
        return getPlan(planID)
                .unassignActivity(activityID);
    }

    @Override
    public boolean assignUserToActivity(int userID, int activityID) {
        if (!hasUserWithThisID(userID) || !hasActivityWithThisID(activityID)) {
            return false;
        }
        return getActivity(activityID)
                .assignUser(userID);
    }

    @Override
    public boolean unassignUserFromActivity(int userID, int activityID) {
        if (!hasUserWithThisID(userID) || !hasActivityWithThisID(activityID)) {
            return false;
        }
        return getActivity(activityID)
                .unassignUser(userID);
    }

    @Override
    public boolean deleteUser(int userID) {
        getAllActivitiesIDs()
                .forEach(x -> unassignUserFromActivity(userID, x));
        return removeUser(userID);
    }

    @Override
    public boolean deleteActivity(int activityID) {
        getAllPlansIDs()
                .forEach(x -> unassignActivityFromPlan(activityID, x));
        return removeActivity(activityID);
    }

    @Override
    public boolean deletePlan(int planID) {
        return removePlan(planID);
    }

    @Override
    public List<Integer> getAllPlansIDs() {
        return org.getPlans().stream()
                .map(Plan::getId)
                .collect(Collectors.toList());
    }

    @Override
    public List<Integer> getAllActivitiesIDs() {
        return org.getActivities().stream()
                .map(Activity::getId)
                .collect(Collectors.toList());
    }

    @Override
    public List<Integer> getAllUsersIDs() {
        return org.getUsers().stream()
                .map(User::getId)
                .collect(Collectors.toList());
    }

    @Override
    public List<Plan> getAllPlans() {
        return new ArrayList<>(org.getPlans());
    }

    @Override
    public List<Activity> getAllActivities() {
        return new ArrayList<>(org.getActivities());
    }

    @Override
    public List<User> getAllUsers() {
        return new ArrayList<>(org.getUsers());
    }

    @Override
    public Set<User> getUsersSet() {
        return org.getUsers();
    }

    @Override
    public Set<Activity> getActivitiesSet() {
        return org.getActivities();
    }

    @Override
    public Set<Plan> getPlansSet() {
        return org.getPlans();
    }

    private boolean addPlan(Plan plan) {
        if (hasPlan(plan)) {
            return false;
        }
        org.getPlans()
                .add(plan);
        return true;
    }

    private boolean addActivity(Activity activity) {
        if (hasActivity(activity)) {
            return false;
        }
        org.getActivities()
                .add(activity);
        return true;
    }

    private boolean addUser(User user) {
        if (hasUser(user)) {
            return false;
        }
        org.getUsers()
                .add(user);
        return true;
    }

    private boolean removePlan(int planID) {
        if (!hasPlanWithThisID(planID)) {
            return false;
        }
        org.getPlans()
                .remove(getPlan(planID));
        return true;
    }

    private boolean removeActivity(int activityID) {
        if (!hasActivityWithThisID(activityID)) {
            return false;
        }
        org.getActivities()
                .remove(getActivity(activityID));
        return true;
    }

    private boolean removeUser(int userID) {
        if (!hasUserWithThisID(userID)) {
            return false;
        }
        org.getUsers()
                .remove(getUser(userID));
        return true;
    }
}