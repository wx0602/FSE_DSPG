package com.korpodrony.menu;

import com.korpodrony.service.PlansService;
import com.korpodrony.utils.IoTools;

class SchedulesMenu {

    private PlansService plansService = new PlansService();

    void startSchedulesMenu() {
        do {
            Messages.printSchedulesMenu();
            int choice = IoTools.getIntFromUser();
            decide(choice);
        } while (!MainMenu.contextMenuExit);
    }

    private void decide(int choice) {
        switch (choice) {
            case 1: {
                addSchedule();
                break;
            }
            case 2: {
                editSchedule();
                break;
            }
            case 3: {
                deleteSchedule();
                break;
            }
            case 4: {
                showSchedules();
                break;
            }
            case 5: {
                assignActivity();
                break;
            }
            case 6: {
                unassignActivity();
                break;
            }
            case 7: {
                showActivitiesOfSchedule();
                break;
            }
            case 8: {
                MainMenu.contextMenuExit = true;
                break;
            }
            default: {
                Messages.printBadInputErrorMessage();
            }
        }
    }

    private void showActivitiesOfSchedule() {
        System.out.println("-- Pokazywanie zajęć przypisanych do planu --");
        plansService.showActivitiesOfSchedule();
    }

    private void unassignActivity() {
        System.out.println("-- Usuwanie zajęć z planu --");
        plansService.unassignActivityFromPlan();
    }

    private void assignActivity() {
        System.out.println("-- Przypisywanie zajęc do planu --");
        plansService.assignActivityToPlan();
    }

    private void addSchedule() {
        System.out.println("-- Dodawanie nowych planów --");
        plansService.addPlan();
    }

    private void editSchedule() {
        System.out.println("-- Edytowanie istniejących planów --");
        plansService.editPlan();
    }

    private void deleteSchedule() {
        System.out.println("-- Usuwanie istniejących planów --");
        plansService.removePlan();
    }

    private void showSchedules() {
        System.out.println("-- Pokazywanie istniejących planów --");
        plansService.printPlans();
    }
}