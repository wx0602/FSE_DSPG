package com.korpodrony.service;

import com.korpodrony.comparators.ActivityIDComparator;
import com.korpodrony.comparators.UserIDComparator;
import com.korpodrony.dao.OrganizationRepositoryDao;
import com.korpodrony.dao.OrganizationRepositoryDaoImpl;
import com.korpodrony.model.ActivitiesType;
import com.korpodrony.model.Activity;
import com.korpodrony.model.User;
import com.korpodrony.utils.IoTools;

import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;
import java.util.stream.Collectors;

import static java.lang.System.out;

public class ActivitiesService {
    private OrganizationRepositoryDao dao = new OrganizationRepositoryDaoImpl();
    private UsersService usersService = new UsersService();

    public void showAssignedUsers() {
        printActivities();
        if (!dao.getAllActivities().isEmpty()) {
            int choice = IoTools.getIntFromUserWithMessage("Podaj ID zajęć, których użytkowników chcesz obejrzeć:");
            if (checkWithMessageOnFalse(dao.hasActivityWithThisID(choice), "Nie ma takich zajęć.")) {
                List<User> users = getUsersFromActivity(choice);
                if (checkWithMessageOnFalse(!users.isEmpty(), "Zajęcia nie mają przypisanych żadnych użytkowników!"))
                    users.sort(new UserIDComparator());
                users.forEach(out::println);
            }
        }
    }

    public void printActivities() {
        printActivities(new ActivityIDComparator());
    }

    public void assignUserToActivity() {
        if (checkWithMessageOnFalse(!dao.getAllActivities().isEmpty() && !dao.getAllUsers().isEmpty()
                , "Nie ma obecnie żadnych zajęć lub użytkowników.")) {
            int activityID = chooseActivity();
            if (checkWithMessageOnFalse(!chooseAvailableUsers(activityID).isEmpty(), "Nie ma obecnie żadnych użytkowników, których można przypisać.")) {
                List<User> availableUsers = chooseAvailableUsers(activityID);
                availableUsers.sort(new UserIDComparator());
                availableUsers.forEach(out::println);
                int userID = IoTools.getIntFromUserWithMessage("Podaj ID użytkownika, którego chcesz przypisać do zajęć:");
                if (canAssignUserToActivity(userID, activityID) && dao.assignUserToActivity(userID, activityID)) {
                    out.println("Przypisano użytkownika do zajęć.");
                }
            }
        }
    }

    public void unassignUserFromActivity() {
        if (checkWithMessageOnFalse(!dao.getAllActivities().isEmpty() && !dao.getAllUsers().isEmpty(), "Nie ma obecnie żadnych zajęć lub użytkowników.")) {
            int activityID = chooseActivity();
            if (checkWithMessageOnFalse(!dao.getActivity(activityID).getAssignedUsersIDs().isEmpty(), "Zajęcia nie posiadają przypisanych użytkowników.")) {
                getAssignedUsers(activityID).forEach(out::println);
                int userID = IoTools.getIntFromUserWithMessage("Podaj ID użytkownika do wypisania z zajęć:");
                if (canUnassignUserFromActivity(userID, activityID) || dao.unassignUserFromActivity(userID, activityID)) {
                    out.println("Użytkownika wypisano z zajęć.");
                }
            }
        }
    }

    public void addActivity() {
        String name = IoTools.getStringFromUserWithMessage("Podaj nazwę zajęć:");
        short maxUsers = IoTools.getShortFromUserWithMessage("Podaj maksymalną liczbę użytkowników zajęć:");
        byte lenghtInQuarters = IoTools.getByteFromUserWithMessage("Podaj czas trwania zajęć wyrażony w kwadransach:");
        ActivitiesType chosenActivity = choosingActivityType();
        if (dao.createActivity(name, maxUsers, lenghtInQuarters, chosenActivity)) {
            out.println("Dodano zajęcia");
        } else {
            out.println("Takie zajęcia już istnieją");
        }
    }

    public void searchActivity() {
        out.println("- Wpisz nazwę:");
        String searchedText = IoTools.getCharsOnlyStringFromUser().toLowerCase();
        List<Activity> activities = getActivitiesByText(searchedText);
        if (checkWithMessageOnFalse(!activities.isEmpty(), "Nie ma takich zajęć.")) {
            printActivities(activities);
        }
    }

    public void printActivities(List<Activity> activities) {
        activities.sort(new ActivityIDComparator());
        activities.forEach(out::println);
    }

    public List<Activity> getActivitiesByIDs(Set<Integer> activities) {
        return activities.stream()
                .map(x -> dao.getActivity(x))
                .collect(Collectors.toList());
    }

    public void editActivity() {
        if (checkWithMessageOnFalse(!dao.getAllActivities().isEmpty(), "Nie ma obecnie żadnych zajęć, które można by edytować.")) {
            printActivities();
            int activityID = IoTools.getIntFromUserWithMessage("Podaj ID zajęć, które chcesz edytować:");
            if (checkWithMessageOnFalse(dao.getAllActivitiesIDs().contains(activityID), "Nie ma zajęć o takim ID.")) {
                out.println("Poprzednia nazwa " + dao.getActivity(activityID).getName());
                String name = IoTools.getStringFromUserWithMessage("Podaj nazwę zajęć:");
                out.println("Poprzednia maksymalną liczbę użytkowników zajęć: " + dao.getActivity(activityID).getMaxUsers());
                short maxUsers = IoTools.getShortFromUserWithMessage("Podaj maksymalną liczbę użytkowników zajęć:");
                out.println("Poprzedni czas trwania zajęć [min]: " + dao.getActivity(activityID).getLengthInQuarters() * 15);
                byte lenghtInQuarters = IoTools.getByteFromUserWithMessage("Podaj czas trwania zajęć wyrażony w kwadransach:");
                out.println("Poprzedni typ zajęć: " + dao.getActivity(activityID).getActivitiesType().getPolishName());
                ActivitiesType chosenActivity = choosingActivityType();
                if (dao.editActivity(activityID, name, maxUsers, lenghtInQuarters, chosenActivity)) {
                    out.println("Zedytowano zajęcia");
                }
            }
        }
    }

    public void removeActivity() {
        printActivities();
        if (!dao.getAllActivities().isEmpty()) {
            int choice = IoTools.getIntFromUserWithMessage("Podaj ID zajęć do usunięcia:");
            if (dao.deleteActivity(choice)) {
                out.println("Usunięto zajęcia.");
            } else {
                out.println("Wybrane zajęcia nie istnieją!");
            }
        }
    }

    private void printActivities(Comparator comparator) {
        List<Activity> activities = dao.getAllActivities();
        activities.sort(comparator);
        if (checkWithMessageOnFalse(!activities.isEmpty(), "Nie ma obecnie żadnych zajęć")) {
            int typeChoice = IoTools.getIntFromUserWithMessage("Podaj numer, by wybrać rodzaj zajęć (1 - wykład, 2 - ćwiczenia, 3- warsztaty, 4 - wszystkie): ");
            activityTypeDecide(typeChoice, activities);
        }
    }

    private boolean checkWithMessageOnFalse(boolean statement, String message) {
        if (!statement) {
            out.println(message);
            return false;
        }
        return true;
    }

    private List<User> chooseAvailableUsers(int actityID) {
        Set<Integer> activityUser = dao.getActivity(actityID).getAssignedUsersIDs();
        return dao.getAllUsers().stream()
                .filter(x -> !activityUser.contains(x.getId()))
                .collect(Collectors.toList());
    }

    private boolean canAssignUserToActivity(int userID, int activityID) {
        if (!dao.hasUserWithThisID(userID)) {
            out.println("Użytkownik z takim ID nie istnieje!");
            return false;
        } else if (dao.getActivity(activityID).getAssignedUsersIDs().contains(userID)) {
            out.println("Ten użytkownik jest już przypisany do zajęć.");
            return false;
        } else if (dao.getActivity(activityID).getAssignedUsersIDs().size() == dao.getActivity(activityID).getMaxUsers()) {
            out.println("Te zajęcia posiadają już maksymalną liczbę przypisanych użytkowników!");
            return false;
        }
        return true;
    }

    private int chooseActivity() {
        printActivities();
        int choice = 0;
        out.println("Podaj ID zajęć:");
        while (!dao.hasActivityWithThisID(choice)) {
            choice = IoTools.getIntFromUser();
            if (!dao.hasActivityWithThisID(choice)) {
                out.println("Nie ma zajęć o takim ID.");
            }
        }
        return choice;
    }

    private List<User> getAssignedUsers(int activityID) {
        return usersService
                .getUsersByIDs(dao.getActivity(activityID)
                        .getAssignedUsersIDs());
    }

    private ActivitiesType choosingActivityType() {
        ActivitiesType chosenActivityType = null;
        do {
            try {
                chosenActivityType = ActivitiesType.getActivity(IoTools
                        .getIntFromUserWithMessage("Podaj numer, by wybrać rodzaj zajęć (1 - wykład, 2 - ćwiczenia, 3- warsztaty)"));
            } catch (ArrayIndexOutOfBoundsException ex) {
                out.println("Podany numer zajęć jest nieprawidłowy.");
            }
        } while (chosenActivityType == null);
        return chosenActivityType;
    }

    private List<Activity> getActivitiesByText(String searchedText) {
        return dao.getAllActivities().stream()
                .filter(x -> x.getName().toLowerCase().contains(searchedText))
                .collect(Collectors.toList());
    }

    private List<User> getUsersFromActivity(int choice) {
        return dao.getActivity(choice)
                .getAssignedUsersIDs()
                .stream()
                .map(x -> dao.getUser(x))
                .collect(Collectors.toList());
    }

    private boolean canUnassignUserFromActivity(int userID, int activityID) {
        if (!dao.getAllUsersIDs().contains(userID)) {
            out.println("Użytkownik o takim ID nie istnieje.");
            return false;
        } else if (!dao.getActivity(activityID).getAssignedUsersIDs().contains(userID)) {
            out.println("Użytkownik nie jest przypisany do tych zajęć, więc nie może być usunięty.");
            return false;
        }
        return true;
    }

    private void activityTypeDecide(int typeChoice, List<Activity> activities) {
        switch (typeChoice) {
            case 1: {
                Predicate<Activity> filter = a -> a.getActivitiesType().equals(ActivitiesType.LECTURE);
                printFilteredActivities(filter, activities);
                break;
            }
            case 2: {
                Predicate<Activity> filter = a -> a.getActivitiesType().equals(ActivitiesType.EXERCISE);
                printFilteredActivities(filter, activities);
                break;
            }
            case 3: {
                Predicate<Activity> filter = a -> a.getActivitiesType().equals(ActivitiesType.WORKSHOP);
                printFilteredActivities(filter, activities);
                break;
            }
            default: {
                Predicate<Activity> filter = a -> true;
                printFilteredActivities(filter, activities);
            }
        }
    }

    private void printFilteredActivities(Predicate<Activity> filter, List<Activity> activities) {
        List<Activity> activityList = filterActivities(filter, activities);
        if (checkWithMessageOnFalse(!activityList.isEmpty(), "Nie ma zajęć spełniających podane kryteria.")) {
            activityList.forEach(out::println);
        }
    }

    private List<Activity> filterActivities(Predicate<Activity> filter, List<Activity> activities) {
        return activities.stream()
                .filter(filter)
                .collect(Collectors.toList());
    }
}