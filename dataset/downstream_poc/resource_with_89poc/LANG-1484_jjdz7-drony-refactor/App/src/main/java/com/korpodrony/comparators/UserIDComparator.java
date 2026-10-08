package com.korpodrony.comparators;

import com.korpodrony.model.User;

import java.util.Comparator;

public class UserIDComparator implements Comparator {

    @Override
    public int compare(Object o, Object t1) {
        User usr1 = (User) o;
        User usr2 = (User) t1;
        return usr1.getId() - usr2.getId();
    }
}