package com.korpodrony.service;

import com.korpodrony.comparators.ActivityIDComparator;
import com.korpodrony.comparators.UserIDComparator;
import com.korpodrony.dao.OrganizationRepositoryDao;
import com.korpodrony.dao.OrganizationRepositoryDaoImpl;
import com.korpodrony.model.Activity;
import com.korpodrony.model.User;
import com.korpodrony.utils.IoTools;

import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static java.lang.System.out;

public class UsersService {

    private OrganizationRepositoryDao dao = new OrganizationRepositoryDaoImpl();

    public void addUser() {
        String name = IoTools.getStringFromUserWithMessage("Podaj imię:");
        String surname = IoTools.getStringFromUserWithMessage("Podaj nazwisko:");
        if (dao.createUser(name, surname)) {
            out.println("Dodano użytkownika.");
        } else {
            out.println("Podany użytkownik już istnieje!");
        }
    }

    public void removeUser() {
        printUsers();
        if (dao.getAllUsers().isEmpty()) {
            return;
        }
        int choice = IoTools.getIntFromUserWithMessage("Podaj ID użytkownika do usunięcia:");
        if (dao.deleteUser(choice)) {
            out.println("Usunięto użytkownika.");
        } else {
            out.println("Użytkownik o takim ID nie istnieje!");
        }
    }

    public void editUser() {
        if (checkWithMessageOnFalse(!dao.getAllUsers().isEmpty(), "Nie ma obecnie żadnych użytkowników, których można by edytować.")) {
            printUsers();
            int userID = IoTools.getIntFromUserWithMessage("Podaj ID użytkownika, który chcesz edytować:");
            if (checkWithMessageOnFalse(dao.hasUserWithThisID(userID), "Nie ma użytkownika o takim ID!")) {
                out.println("Poprzednie imię użytkownika: " + dao.getUser(userID).getName());
                String name = IoTools.getStringFromUserWithMessage("Podaj nowe imię użytkownika:");
                out.println("Poprzednie naziwsko użytkownika: " + dao.getUser(userID).getSurname());
                String surName = IoTools.getStringFromUserWithMessage("Podaj nowe nazwisko użytkownika:");
                if (dao.editUser(userID, name, surName)) {
                    out.println("Zedytowano użytkownika.");
                }
            }
        }
    }

    public void showUserActivities() {
        printUsers();
        if (!dao.getAllUsers().isEmpty()) {
            int choice = IoTools.getIntFromUserWithMessage("Podaj ID użytkownika, do którego zajęcia chcesz obejrzeć:");
            if (checkWithMessageOnFalse(dao.hasUserWithThisID(choice), "Nie ma takiego użytkownika.")) {
                List<Activity> userActivities = dao.getAllActivities().stream()
                        .filter(x -> x.getAssignedUsersIDs().contains(choice))
                        .collect(Collectors.toList());
                if (checkWithMessageOnFalse(!userActivities.isEmpty(), "Użytkownik nie jest przypisany do żadnych zajęć.")) {
                    userActivities.sort(new ActivityIDComparator());
                    userActivities.forEach(out::println);
                }
            }
        }
    }

    public void printUsers() {
        printUsers(new UserIDComparator());
    }

    public void printUsers(Comparator comparator) {
        List<User> users = dao.getAllUsers();
        users.sort(comparator);
        if (checkWithMessageOnFalse(!users.isEmpty(), "Nie ma obecnie żadnych użytkowników.")) {
            users.forEach(out::println);
        }
    }

    public void searchUsersByName() {
        out.println("- Wpisz imię:");
        String name = IoTools.getCharsOnlyStringFromUser()
                .toLowerCase();
        List<User> users = dao.getAllUsers().stream()
                .filter(x -> x.getName().toLowerCase().contains(name))
                .collect(Collectors.toList());
        if (checkWithMessageOnFalse(!users.isEmpty(), "Nie ma takiego użytkownika.")) {
            users.sort(new UserIDComparator());
            users.forEach(out::println);
        }
    }

    public List<User> getUsersByIDs(Set<Integer> users) {
        return users.stream()
                .map(x -> dao.getUser(x))
                .collect(Collectors.toList());
    }

    private boolean checkWithMessageOnFalse(boolean statement, String message) {
        if (!statement) {
            out.println(message);
            return false;
        }
        return true;
    }
}