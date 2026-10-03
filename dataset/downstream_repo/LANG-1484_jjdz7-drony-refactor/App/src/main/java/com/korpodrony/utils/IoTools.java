package com.korpodrony.utils;

import java.util.ArrayList;
import java.util.Locale;
import java.util.Scanner;

import static java.lang.System.in;
import static java.lang.System.out;

public class IoTools {

    private static final Scanner sc = new Scanner(in).useLocale(Locale.US);

    public static String getCharsOnlyStringFromUser() {
        String text = "";
        while (Validator.notContainsOnlyLetters(text)) {
            text = sc.nextLine();
            if (Validator.notContainsOnlyLetters(text)) {
                out.println("Tylko litery są dozwolone. Spróbuj ponownie: ");
            }
        }
        return text;
    }

    public static String getStringFromUserWithMessage(String message) {
        out.println(message);
        return getCharsOnlyStringFromUser();
    }

    public static short getShortFromUser() {
        short number = 0;
        while (!sc.hasNextShort()) {
            out.println(sc.next() + ": nie jest liczbą z zakresu 1 do 32767. Spróbuj ponownie:");
        }
        number = sc.nextShort();
        return number;
    }

    public static short getShortFromUserWithMessage(String message) {
        out.println(message);
        short number = 0;
        while (Validator.isNotPositive(number)) {
            number = getShortFromUser();
            if (Validator.isNotPositive(number)) {
                out.println("Nie można przekazać wartości mniejszej od 1. Spróbuj ponownie:");
            }
        }
        return number;
    }

    public static byte getByteFromUser() {
        byte number = 0;
        while (!sc.hasNextByte()) {
            out.println(sc.next() + ": nie jest liczbą z zakresu 1 do 127. Spróbuj ponownie:");
        }
        number = sc.nextByte();
        return number;
    }

    public static byte getByteFromUserWithMessage(String message) {
        out.println(message);
        byte number = 0;
        while (Validator.isNotPositive(number)) {
            number = getByteFromUser();
            if (Validator.isNotPositive(number)) {
                out.println("Nie można przekazać wartości mniejszej od 1. Spróbuj ponownie:");
            }
        }
        return number;
    }

    public static int getIntFromUser() {
        int number = 0;
        out.println("Twój wybór?");
        while (Validator.isNotPositive(number)) {
            while (!sc.hasNextInt()) {
                out.println(sc.next() + ": nie jest liczbą. Spróbuj ponownie:");
                sc.nextLine();
            }
            number = sc.nextInt();
            sc.nextLine();
            if (Validator.isNotPositive(number)) {
                out.println("Podana wartość musi być większa od zera. Spróbuj ponownie");
            }
        }
        return number;
    }

    public static int getIntFromUserWithMessage(String message) {
        out.println(message);
        return getIntFromUser();
    }
}