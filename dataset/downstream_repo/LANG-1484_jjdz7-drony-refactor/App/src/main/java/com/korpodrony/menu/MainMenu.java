package com.korpodrony.menu;


import com.korpodrony.service.RepositoryService;
import com.korpodrony.utils.IoTools;

public class MainMenu {
    private static boolean exit;
    static boolean contextMenuExit;
    static boolean subMenuExit;
    static int menuIdToSearch;

    public void startMainMenu() {
        do {
            contextMenuExit = false;
            Messages.printMainMenu();
            int choice = IoTools.getIntFromUser();
            runMainMenuDecide(choice);
        } while (!exit);
            new RepositoryService().writeRepositoryToFile();
    }

    private void runMainMenuDecide(int choice) {
        switch (choice) {
            case 1: {
                new SearchMenu().startSearchMenu();
                break;
            }
            case 2: {
                new UsersMenu().startUsersMenu();
                break;
            }
            case 3: {
                new ActivitiesMenu().startActivitiesMenu();
                break;
            }
            case 4: {
                 new SchedulesMenu().startSchedulesMenu();
                break;
            }
            case 5: {
                exit = true;
                break;
            }
            default: {
                Messages.printBadInputErrorMessage();
            }
        }
    }
}