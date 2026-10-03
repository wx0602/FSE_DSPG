package com.korpodrony.dao;

import com.korpodrony.model.Plan;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public interface PlanRepositoryDao {

    boolean createPlan(String name);

    boolean assignActivityToPlan(int activityID, int planID);

    boolean unassignActivityFromPlan(int activityID, int planID);

    boolean deletePlan(int planID);

    Plan getPlan(int planID);

    boolean editPlan(int planID, String name);

    default List<Integer> getAllPlansIDs() {
        return new ArrayList<>();
    }

    List<Plan> getAllPlans();

    default boolean hasPlan(Plan plan) {
        return false;
    }

    boolean hasPlanWithThisID(int planID);

    default Set<Plan> getPlansSet() {
        return null;
    }
}