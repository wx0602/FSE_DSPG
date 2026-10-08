package com.korpodrony.menu;

import com.korpodrony.service.UsersService;
import com.korpodrony.utils.IoTools;

class UsersMenu {
    private UsersService usersService = new UsersService();

    void startUsersMenu() {
        do {
            Messages.printUsersMenu();
            int choice = IoTools.getIntFromUser();
            decide(choice);
        } while (!MainMenu.contextMenuExit);
    }

    private void decide(int choice) {
        switch (choice) {
            case 1: {
                addUser();
                break;
            }
            case 2: {
                editUser();
                break;
            }
            case 3: {
                deleteUser();
                break;
            }
            case 4: {
                showUser();
                break;
            }
            case 5: {
                showUserActivities();
                break;
            }
            case 6: {
                MainMenu.contextMenuExit = true;
                break;
            }
            default: {
                Messages.printBadInputErrorMessage();
            }

        }
    }

    private void showUserActivities() {
        System.out.println("-- Pokazywanie zajęć użytkownika --");
        usersService.showUserActivities();

    }

    private void addUser() {
        System.out.println("-- Dodawanie nowego użytkownika --");
        usersService.addUser();
    }

    private void editUser() {
        System.out.println("-- Edytowanie użytkownika --");
        usersService.editUser();
    }

    private void deleteUser() {
        System.out.println("-- Usuwanie użytkownika --");
        usersService.removeUser();
    }

    private void showUser() {
        usersService.printUsers();
    }
}