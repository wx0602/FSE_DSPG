package com.korpodrony.services;

import com.korpodrony.daoInterfaces.ActivityRepositoryDaoInterface;
import com.korpodrony.dto.ActivityDTO;
import com.korpodrony.dto.SimplifiedActivityDTO;
import com.korpodrony.dto.UserDTO;
import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.entity.builder.ActivityEntityBuilder;
import com.korpodrony.model.ActivitiesType;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.inject.Inject;
import java.util.HashSet;
import java.util.List;
import java.util.stream.Collectors;

@RequestScoped
public class ActivitiesWebService {

    Logger logger = LoggerFactory.getLogger("com.korpodrony.services");

    @EJB
    ActivityRepositoryDaoInterface activityRepositoryDao;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    public boolean hasActivity(int activityId) {
        logger.debug("Has Activity called");
        return activityRepositoryDao.hasActivityWithThisID(activityId);
    }

    public List<SimplifiedActivityDTO> getAllActivities() {
        logger.debug("Getting AllSimplifiedActivities called");
        return activityRepositoryDao.getAllSimplifiedActivates();
    }

    public List<SimplifiedActivityDTO> getAllUserActivities(int userId) {
        logger.debug("Getting AllSimplifiedActivities called");
        return activityRepositoryDao.getAllUserSimplifiedActivates(userId);
    }

    public ActivityDTO getActivityDTO(int activityId) {
        logger.debug("Getting activityDTO called");
        return activityRepositoryDao.getActivityDTO(activityId);
    }

    public boolean assignUsersToActivity(List<Integer> usersIds, int activityId) {
        ActivityEntity activityEntity = activityRepositoryDao.getActivityEntityWithRelations(activityId);
        logger.debug("activityEntity: " + activityEntity);
        logger.debug("users ids: " + usersIds);
        if (activityEntity != null && usersIds != null) {
            if (activityEntity.getAssigned_users() == null) {
                activityEntity.setAssigned_users(new HashSet<>());
                logger.debug("new HashSet created");
            }
            List<Integer> userIdsListToAssign = getUserIdsListToAssign(usersIds, activityEntity);
            activityRepositoryDao.getUsersEntitiesList(userIdsListToAssign).forEach(x -> activityEntity.getAssigned_users()
                    .add(x)
            );
            activityRepositoryDao.updateActivity(activityEntity);
            logger.debug("usersEntities assigned to Activity");
            return true;
        }
        return false;
    }

    public boolean unassignUsersFromActivity(List<Integer> usersIds, int activityId) {
        ActivityEntity activityEntity = activityRepositoryDao.getActivityEntityWithRelations(activityId);
        logger.debug("activityEntity: " + activityEntity);
        logger.debug("userIds " + usersIds);
        if (activityEntity != null && usersIds != null) {
            if (activityEntity.getAssigned_users() == null) {
                logger.debug("no assigned users to activity");
                return false;
            }
            activityEntity.setAssigned_users(activityEntity.getAssigned_users()
                    .stream()
                    .filter(x -> !usersIds.contains(x.getId()))
                    .collect(Collectors.toSet())
            );
            activityRepositoryDao.updateActivity(activityEntity);
            logger.debug("usersEntities unassigned from Activity");
            return true;
        }
        return false;
    }

    public boolean deleteActivity(int activityId) {
        logger.debug("Deleting user called");
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.ACTIVITIES, Action.DELETE);
        return activityRepositoryDao.deleteActivity(activityId);
    }

    public boolean editActivity(int activityId, String name, short maxUsers, byte duration, int activityTypeNumber) {
        logger.debug("Editing activity called");
        ActivityEntity activityEntity = activityRepositoryDao.getActivityEntity(activityId);
        if (activityEntity == null) {
            return false;
        }
        activityEntity.setName(name);
        activityEntity.setMaxUsers(maxUsers);
        activityEntity.setLengthInQuarters(duration);
        activityEntity.setActivitiesType(ActivitiesType.getActivity(activityTypeNumber));
        activityRepositoryDao.updateActivity(activityEntity);
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.ACTIVITIES, Action.EDIT);
        return true;
    }

    public int createActivity(String name, short maxUsers, byte duration, int activityType) {
        logger.debug("Creating user called");
        ActivityEntity activityEntity = ActivityEntityBuilder.anActivityEntity()
                .withName(name)
                .withMaxUsers(maxUsers)
                .withLengthInQuarters(duration)
                .withActivitiesType(ActivitiesType.getActivity(activityType))
                .build();
        activityRepositoryDao.createActivity(activityEntity);
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.ACTIVITIES, Action.ADD);
        return activityEntity.getId();
    }

    public List<UserDTO> getAvailableUserDTO(int activityId) {
        logger.debug("Getting getAvailableUsersDTO called");
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.ACTIVITIES, Action.GET_AVAILABLE_LIST);
        return activityRepositoryDao.getAvailableUsersDTO(activityId);
    }

    public List<SimplifiedActivityDTO> getAllActivitiesByActivityType(ActivitiesType activity) {
        logger.debug("Getting AllSimplifiedActivities by ActivitiesType called");
        return activityRepositoryDao.getAllSimplifiedActivates(activity);
    }

    private List<Integer> getUserIdsListToAssign(List<Integer> usersIds, ActivityEntity activityEntity) {
        int numberOfPlaces = activityEntity.getMaxUsers() - activityEntity.getAssigned_users().size();
        if (numberOfPlaces < usersIds.size()) {
            return usersIds.subList(0, numberOfPlaces);
        }
        return usersIds;
    }
}