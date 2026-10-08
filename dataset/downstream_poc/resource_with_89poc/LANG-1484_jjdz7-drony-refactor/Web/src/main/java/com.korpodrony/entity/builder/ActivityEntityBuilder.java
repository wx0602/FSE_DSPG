package com.korpodrony.entity.builder;

import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.model.ActivitiesType;

public final class ActivityEntityBuilder {
    private String name;
    private short maxUsers;
    private byte lengthInQuarters;
    private ActivitiesType activitiesType;

    private ActivityEntityBuilder() {
    }

    public static ActivityEntityBuilder anActivityEntity() {
        return new ActivityEntityBuilder();
    }

    public ActivityEntityBuilder withName(String name) {
        this.name = name;
        return this;
    }

    public ActivityEntityBuilder withMaxUsers(short maxUsers) {
        this.maxUsers = maxUsers;
        return this;
    }

    public ActivityEntityBuilder withLengthInQuarters(byte lengthInQuarters) {
        this.lengthInQuarters = lengthInQuarters;
        return this;
    }

    public ActivityEntityBuilder withActivitiesType(ActivitiesType activitiesType) {
        this.activitiesType = activitiesType;
        return this;
    }

    public ActivityEntity build() {
        ActivityEntity activityEntity = new ActivityEntity();
        activityEntity.setName(name);
        activityEntity.setMaxUsers(maxUsers);
        activityEntity.setLengthInQuarters(lengthInQuarters);
        activityEntity.setActivitiesType(activitiesType);
        return activityEntity;
    }
}
