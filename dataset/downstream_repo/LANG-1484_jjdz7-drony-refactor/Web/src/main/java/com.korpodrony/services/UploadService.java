package com.korpodrony.services;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.korpodrony.daoInterfaces.ActivityRepositoryDaoInterface;
import com.korpodrony.daoInterfaces.PlanRepositoryDaoInterface;
import com.korpodrony.daoInterfaces.UserRepositoryDaoInterface;
import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.entity.PlanEntity;
import com.korpodrony.entity.UserEntity;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.EJB;
import javax.enterprise.context.ApplicationScoped;
import javax.inject.Inject;
import java.io.*;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Collectors;

@ApplicationScoped
public class UploadService {

    @EJB
    UserRepositoryDaoInterface userRepositoryDao;

    @EJB
    ActivityRepositoryDaoInterface activityRepositoryDao;

    @EJB
    PlanRepositoryDaoInterface planRepositoryDao;

    @Inject
    PlansWebService plansWebService;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.services");


    public void uploadFile(InputStream fileContent) throws IOException {
        String fileContentString = extractFileContentString(fileContent);
        logger.debug("file context: " + fileContentString);
        if (uploadUsers(fileContentString)) {
            logger.debug("Users successfully loaded");
            reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.UPLOAD_FILE, Action.USERS_FILE_UPLOAD);
            return;
        } else if (uploadActivities(fileContentString)) {
            logger.debug("Activities successfully loaded");
            reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.UPLOAD_FILE, Action.ACTIVITIES_FILE_UPLOAD);

            return;
        } else if (uploadPlans(fileContentString)) {
            logger.debug("Plans successfully loaded");
            reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.UPLOAD_FILE, Action.PLANS_FILE_UPLOAD);
            return;
        } else {
            logger.debug("No Entities loaded");
            throw new IOException("Niepoprawny plik");
        }
    }

    private String extractFileContentString(InputStream fileContent) throws IOException {
        StringBuilder textBuilder = new StringBuilder();
        try (Reader reader = new BufferedReader(new InputStreamReader
                (fileContent, Charset.forName(StandardCharsets.UTF_8.name())))) {
            int c = 0;
            while ((c = reader.read()) != -1) {
                textBuilder.append((char) c);
            }
        }
        logger.debug("String extracted from file: " + textBuilder.toString());
        return textBuilder.toString();
    }

    private boolean uploadPlans(String json) {
        Set<PlanEntity> planEntitySet = parsePlanEntityFromJSON(json);
        logger.debug("planEntitySet: " + planEntitySet);
        if (planEntitySet.isEmpty()) {
            return false;
        }
        updatePlans(planEntitySet);
        return true;
    }

    private boolean uploadActivities(String json) {
        Set<ActivityEntity> activityEntitySet = parseActivityEntityFromJSON(json);
        logger.debug("activityEntitySet: " + activityEntitySet);
        if (activityEntitySet.isEmpty()) {
            return false;
        }
        updateActivities(activityEntitySet);
        return true;
    }

    private boolean uploadUsers(String json) {
        Set<UserEntity> userEntitySet = parseUserEntityFromJSON(json);
        logger.debug("userEntitySet: " + userEntitySet);
        if (userEntitySet.isEmpty()) {
            return false;
        }
        updateUsers(userEntitySet);
        return true;
    }

    private void updatePlans(Set<PlanEntity> planEntities) {
        logger.debug("Uploading plans");
        preparePlansActivities(planEntities);
        planEntities.forEach(plan -> {
            plan.setId(planRepositoryDao.createPlan(plan));
            plansWebService.assignActivitiesToPlan(plan.getAssignedActivities()
                    .stream()
                    .map(ActivityEntity::getId)
                    .collect(Collectors.toList()), plan.getId()
            );
        });
    }

    private void preparePlansActivities(Set<PlanEntity> planEntities) {
        logger.debug("preparing Activities for uploading plan");
        Map<Integer, Integer> activitiesIds = new HashMap<>();
        planEntities.forEach(plan -> plan.getAssignedActivities()
                .forEach(activityEntity -> {
                            Integer id = activitiesIds.get(activityEntity.getId());
                            logger.debug("Activity id from activitiesIds: " + id + ", activity Id from stream: " + activityEntity.getId());
                            if (id == null) {
                                int oldId = activityEntity.getId();
                                updateActivity(activityEntity);
                                logger.debug("New activity Id from stream: " + activityEntity.getId());
                                activitiesIds.put(oldId, activityEntity.getId());
                            } else {
                                activityEntity.setId(id);
                            }
                        }
                ));
    }

    private void updateActivities(Set<ActivityEntity> activityEntities) {
        logger.debug("Uploading activities: " + activityEntities);
        activityEntities.forEach(this::updateActivity);
    }

    private void updateActivity(ActivityEntity activityEntity) {
        logger.debug("Uploading single activity: " + activityEntity);
        updateActivityUsers(activityEntity);
        activityEntity.setId(activityRepositoryDao.createActivity(activityEntity));
    }

    private void updateActivityUsers(ActivityEntity activityEntity) {
        logger.debug("Updating activity's users: " + activityEntity);
        activityEntity.setAssigned_users(
                updateUsers(activityEntity.getAssigned_users()));
    }

    private Set<UserEntity> updateUsers(Set<UserEntity> users) {
        logger.debug("Updating users:" + users);
        return users.stream().map(this::updateUser).collect(Collectors.toSet());
    }

    private UserEntity updateUser(UserEntity userEntity) {
        logger.debug("Updating user: " + userEntity);
        int userId = userRepositoryDao.getUserIdByEmail(userEntity.getEmail());
        if (userId == 0) {
            userId = userRepositoryDao.createUser(userEntity);
        }
        userEntity.setId(userId);
        userEntity.setPermissionLevel(PermissionLevel.USER);
        return userEntity;
    }

    private Set<UserEntity> parseUserEntityFromJSON(String json) {
        logger.debug("Parsing UserEntity from JSON: " + json);
        ObjectMapper mapper = new ObjectMapper();
        if (json != null) {
            try {
                UserEntity[] readValue = mapper.readValue(json, UserEntity[].class);
                Set<UserEntity> userEntitySet = new HashSet<>(Arrays.asList(readValue));
                return userEntitySet;
            } catch (JsonProcessingException e) {
                System.out.println("PROCESSING_FILE_ERROR");
            }
        } else {
            System.out.println("EMPTY_FILE");
        }
        return Collections.emptySet();
    }

    private Set<ActivityEntity> parseActivityEntityFromJSON(String json) {
        logger.debug("Parsing ActivityEntity from JSON: " + json);

        ObjectMapper mapper = new ObjectMapper();
        if (json != null) {
            try {
                ActivityEntity[] readValue = mapper.readValue(json, ActivityEntity[].class);
                Set<ActivityEntity> activityEntitySet = new HashSet<>(Arrays.asList(readValue));
                return activityEntitySet;
            } catch (JsonProcessingException e) {
                System.out.println("PROCESSING_FILE_ERROR");
            }
        } else {
            System.out.println("EMPTY_FILE");
        }
        return Collections.emptySet();
    }

    private Set<PlanEntity> parsePlanEntityFromJSON(String json) {
        logger.debug("Parsing PlanEntity from JSON: " + json);
        ObjectMapper mapper = new ObjectMapper();
        if (json != null) {
            try {
                PlanEntity[] readValue = mapper.readValue(json, PlanEntity[].class);
                Set<PlanEntity> planEntitySet = new HashSet<>(Arrays.asList(readValue));
                return planEntitySet;
            } catch (JsonProcessingException e) {
                System.out.println("PROCESSING_FILE_ERROR");
            }
        } else {
            System.out.println("EMPTY_FILE");
        }
        return Collections.emptySet();
    }
}