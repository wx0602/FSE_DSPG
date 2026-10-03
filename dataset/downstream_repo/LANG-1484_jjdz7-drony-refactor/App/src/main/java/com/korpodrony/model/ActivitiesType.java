package com.korpodrony.model;

public enum ActivitiesType {

    LECTURE("wykład",1),
    EXERCISE("ćwiczenia",2),
    WORKSHOP("warszaty",3);

    String polishName;
    int number;

    public String getPolishName() {
        return polishName;
    }

    public int getNumber() {
        return number;
    }

    ActivitiesType(String polishName, int number) {
        this.polishName = polishName;
        this.number = number;
    }

    public static ActivitiesType getActivity(int number) {
        return ActivitiesType.values()[number - 1];
    }
}