package com.korpodrony.menu;

import com.korpodrony.service.ActivitiesService;
import com.korpodrony.service.PlansService;
import com.korpodrony.service.UsersService;
import com.korpodrony.utils.IoTools;

class SearchMenu {
    private UsersService usersService = new UsersService();
    private ActivitiesService activitiesService = new ActivitiesService();
    private PlansService plansService = new PlansService();

    void startSearchMenu() {

        do {
            Messages.printSearchMenu();
            int choice = IoTools.getIntFromUser();
            decide(choice);
        } while (!MainMenu.contextMenuExit);
    }

    private void decide(int choice) {
        switch (choice) {
            case 1: {
                searchByUserMenu();
                break;
            }
            case 2: {
                searchByActivityMenu();
                break;
            }
            case 3: {
                searchByScheduleMenu();
                break;
            }
            case 4: {
                MainMenu.contextMenuExit = true;
                break;
            }
            default: {
                Messages.printBadInputErrorMessage();
            }

        }
    }

    private void searchByUserMenu() {
        System.out.println("-- Szukanie użytkownika po imieniu");
        usersService.searchUsersByName();
    }

    private void searchByActivityMenu() {
        System.out.println("-- Szukanie zajęć po nazwie");
        activitiesService.searchActivity();
    }

    private void searchByScheduleMenu() {
        System.out.println("-- Szukanie planu po nazwie");
        plansService.searchPlan();
    }
}