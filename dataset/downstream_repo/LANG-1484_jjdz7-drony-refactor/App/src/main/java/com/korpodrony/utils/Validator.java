package com.korpodrony.utils;

public class Validator {
    private Validator() {
    }

    public static boolean notContainsOnlyLetters(String text) {
        return !text.chars().allMatch(Character::isLetter) || text.equals("");
    }

    public static boolean isNotPositive(short number) {
        return number <= 0;
    }

    public static boolean isNotPositive(byte number) {
        return number <= 0;
    }

    public static boolean isNotPositive(int number) {
        return number <= 0;
    }
}