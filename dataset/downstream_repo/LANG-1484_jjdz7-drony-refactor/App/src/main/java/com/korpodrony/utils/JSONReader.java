package com.korpodrony.utils;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.korpodrony.model.Activity;
import com.korpodrony.model.Organization;
import com.korpodrony.model.Plan;
import com.korpodrony.model.User;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

public class JSONReader {

    private static final String PROCESSING_FILE_ERROR = "Błąd w czasie przetwarzania pliku!";

    private static final String EMPTY_FILE = "Plik jest pusty!";

    public static Set<Activity> parseActivityFromJSONFile(Path path) {
        ObjectMapper mapper = new ObjectMapper();
        String jsonString = readJsonStringFromfile(path);
        if (jsonString != null) {
            try {
                Activity[] readValue = mapper.readValue(jsonString, Activity[].class);
                Set<Activity> setOfActivity = new HashSet<>(Arrays.asList(readValue));
                return setOfActivity;
            } catch (JsonProcessingException e) {
                System.out.println(PROCESSING_FILE_ERROR);
            }
        } else {
            System.out.println(EMPTY_FILE);
        }
        return Collections.emptySet();
    }

    public static Set<Organization> parseOrganizationFromJSONFile(Path path) {
        ObjectMapper mapper = new ObjectMapper();
        String jsonString = readJsonStringFromfile(path);
        if (jsonString != null) {
            try {
                Organization[] readValue = mapper.readValue(jsonString, Organization[].class);
                Set<Organization> setOfOrganization = new HashSet<>(Arrays.asList(readValue));
                return setOfOrganization;
            } catch (JsonProcessingException e) {
                System.out.println(PROCESSING_FILE_ERROR);
            }
        } else {
            System.out.println(EMPTY_FILE);
        }
        return Collections.emptySet();
    }

    public static Set<Plan> parsePlanFromJSONFile(Path path) {
        ObjectMapper mapper = new ObjectMapper();
        String jsonString = readJsonStringFromfile(path);
        if (jsonString != null) {
            try {
                Plan[] readValue = mapper.readValue(jsonString, Plan[].class);
                Set<Plan> setOfPlan = new HashSet<>(Arrays.asList(readValue));
                return setOfPlan;
            } catch (JsonProcessingException e) {
                System.out.println(PROCESSING_FILE_ERROR);
            }
        } else {
            System.out.println(EMPTY_FILE);
        }
        return Collections.emptySet();
    }

    public static Set<User> parseUserFromJSONFile(Path path) {
        ObjectMapper mapper = new ObjectMapper();
        String jsonString = readJsonStringFromfile(path);
        if (jsonString != null) {
            try {
                User[] readValue = mapper.readValue(jsonString, User[].class);
                Set<User> setOfUsers = new HashSet<>(Arrays.asList(readValue));
                return setOfUsers;
            } catch (JsonProcessingException e) {
                System.out.println(PROCESSING_FILE_ERROR);
            }
        } else {
            System.out.println(EMPTY_FILE);
        }
        return Collections.emptySet();
    }

    private static String readJsonStringFromfile(Path path) {
        try {
            byte[] allBytesFromFile = Files.readAllBytes(path);
            String readStringFromFile = new String(allBytesFromFile);
            return readStringFromFile;
        } catch (IOException e) {
            System.out.println(PROCESSING_FILE_ERROR);
        }
        return null;
    }
}