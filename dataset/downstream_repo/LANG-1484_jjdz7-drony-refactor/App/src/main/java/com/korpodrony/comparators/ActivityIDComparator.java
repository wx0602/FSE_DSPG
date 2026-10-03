package com.korpodrony.comparators;

import com.korpodrony.model.Activity;

import java.util.Comparator;

public class ActivityIDComparator implements Comparator {
    @Override
    public int compare(Object o, Object t1) {
        Activity act1 = (Activity) o;
        Activity act2 = (Activity) t1;
        return act1.getId() - act2.getId();
    }
}