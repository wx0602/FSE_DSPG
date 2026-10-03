package com.korpodrony.comparators;

import com.korpodrony.model.Plan;

import java.util.Comparator;

public class PlanIDComparator implements Comparator {
    @Override
    public int compare(Object o, Object t1) {
        Plan plan1 = (Plan) o;
        Plan plan2 = (Plan) t1;
        return plan1.getId() - plan2.getId();
    }
}