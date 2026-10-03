package com.korpodrony.dao;

import com.korpodrony.daoInterfaces.ActivityRepositoryDaoInterface;
import com.korpodrony.daoInterfaces.PlanRepositoryDaoInterface;
import com.korpodrony.dto.ActivityDTO;
import com.korpodrony.dto.SimplifiedActivityDTO;
import com.korpodrony.dto.UserDTO;
import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.entity.PlanEntity;
import com.korpodrony.entity.UserEntity;
import com.korpodrony.entity.builder.ActivityEntityBuilder;
import com.korpodrony.model.ActivitiesType;
import org.hibernate.Hibernate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.EJB;
import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;
import java.util.ArrayList;
import java.util.List;

@Stateless
public class ActivityDaoImpl implements ActivityRepositoryDaoInterface {

    @EJB
    PlanRepositoryDaoInterface planRepositoryDao;

    @PersistenceContext(unitName = "korpodrony-hibernate")
    private EntityManager entityManager;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.dao");

    @Override
    public int createActivity(ActivityEntity activity) {
        ActivityEntity activityEntity = ActivityEntityBuilder.anActivityEntity()
                .withName(activity.getName())
                .withMaxUsers(activity.getMaxUsers())
                .withActivitiesType(activity.getActivitiesType())
                .withLengthInQuarters(activity.getLengthInQuarters())
                .build();
        entityManager.persist(activityEntity);
        entityManager.flush();
        logger.info("Created activity with id: " + activityEntity.getId() + " from " + activityEntity);
        activityEntity.setAssigned_users(activity.getAssigned_users());
        logger.info("Users which have been assigned: " + activityEntity.getAssigned_users());
        entityManager.merge(activityEntity);
        return activityEntity.getId();
    }

    @Override
    public void updateActivity(ActivityEntity activityEntity) {
        entityManager.merge(activityEntity);
    }

    public boolean deleteActivity(int activityID) {
        if (hasActivityWithThisID(activityID)) {
            entityManager.createQuery(
                    "select p from Plan p join p.assignedActivities a where a.id=:id", PlanEntity.class)
                    .setParameter("id", activityID)
                    .getResultList()
                    .forEach(x -> planRepositoryDao.unassignActivityFromPlan(activityID, x.getId()));
            entityManager.flush();
            entityManager.createQuery("DELETE FROM Activity a WHERE a.id=:id")
                    .setParameter("id", activityID)
                    .executeUpdate();
            entityManager.flush();
            logger.info("Activity with id: " + activityID + "has been removed");
            return true;
        } else {
            logger.info("Activity with id: " + activityID + "doesn't exist");
            return false;
        }
    }

    public boolean hasActivityWithThisID(int activityID) {
        try {
            Object id = entityManager
                    .createQuery("SELECT a.id FROM Activity a where a.id=:id")
                    .setParameter("id", activityID)
                    .getSingleResult();
            logger.debug("Has activity with id: " + activityID);
            return true;
        } catch (NoResultException e) {
            logger.debug("Doesn't have activity with id: " + activityID);
            return false;
        }
    }

    public List<SimplifiedActivityDTO> getAllSimplifiedActivates() {
        try {
            logger.debug("Getting simplified list of activities");
            return entityManager
                    .createQuery("SELECT new com.korpodrony.dto.SimplifiedActivityDTO(a.id, a.name, a.activitiesType) FROM Activity a", SimplifiedActivityDTO.class)
                    .getResultList();
        } catch (NoResultException e) {
            logger.debug("No activities to make simplified list");
            return new ArrayList<>();
        }
    }

    @Override
    public List<SimplifiedActivityDTO> getAllUserSimplifiedActivates(int userId) {
        logger.debug("Getting all activities where user is assigned: " + userId);
        return entityManager.createQuery("SELECT new com.korpodrony.dto.SimplifiedActivityDTO(a.id, a.name, a.activitiesType)" +
                " from Activity a WHERE a IN (select a from Activity a join a.assigned_users u where u.id=:id)", SimplifiedActivityDTO.class)
                .setParameter("id", userId)
                .getResultList();
    }

    public List<SimplifiedActivityDTO> getAllSimplifiedActivates(ActivitiesType activitiesType) {
        try {
            logger.debug("Getting simplified list of activities which are type of: " + activitiesType);
            return entityManager
                    .createQuery("SELECT new com.korpodrony.dto.SimplifiedActivityDTO(a.id, a.name, a.activitiesType) FROM Activity a WHERE " +
                            "a.activitiesType=:activityType", SimplifiedActivityDTO.class)
                    .setParameter("activityType", activitiesType)
                    .getResultList();
        } catch (NoResultException e) {
            logger.info("No activities which are type of: " + activitiesType + " to make simplified list");
            return new ArrayList<>();
        }
    }

    public ActivityEntity getActivityEntity(int activityId) {
        logger.debug("Getting activityEntity with id: " + activityId);
        return entityManager.find(ActivityEntity.class, activityId);
    }

    @Override
    public ActivityEntity getActivityEntityWithRelations(int activityId) {
        logger.debug("Getting activityEntity with id: " + activityId);
        ActivityEntity activityEntity = entityManager.find(ActivityEntity.class, activityId);
        Hibernate.initialize(activityEntity.getAssigned_users());
        return activityEntity;
    }

    public ActivityDTO getActivityDTO(int activityId) {
        try {
            logger.debug("Getting activityDTO with id: " + activityId);
            return getActivityEntity(activityId)
                    .createActivityDTO();
        } catch (NoResultException e) {
            logger.debug("No activity with id: " + activityId);
            return null;
        }
    }

    public List<UserDTO> getAvailableUsersDTO(int activityId) {
        logger.debug("Getting availableUsersDTOs for Activity with id: " + activityId);
        return entityManager.createQuery("SELECT new com.korpodrony.dto.UserDTO(u.id, u.name, u.surname, u.email)" +
                " from User u WHERE u NOT IN (select u from Activity a join a.assigned_users u where a.id=:id) and u.permissionLevel=:level", UserDTO.class)
                .setParameter("id", activityId)
                .setParameter("level", PermissionLevel.USER)
                .getResultList();
    }

    public List<SimplifiedActivityDTO> getAllSimplifiedActivates(String name) {
        try {
            logger.debug("Getting simplified activities by name: " + name);
            return entityManager
                    .createQuery("SELECT new com.korpodrony.dto.SimplifiedActivityDTO(a.id, a.name, a.activitiesType) FROM Activity a WHERE " +
                            "lower(a.name) like :name", SimplifiedActivityDTO.class)
                    .setParameter("name", "%" + name + "%")
                    .getResultList();
        } catch (NoResultException e) {
            logger.debug("No activities with name: " + name);
            return new ArrayList<>();
        }
    }

    public List<UserEntity> getUsersEntitiesList(List<Integer> usersIds) {
        return entityManager.createQuery("SELECT u from User u WHERE u.id in (:usersIds)", UserEntity.class)
                .setParameter("usersIds", usersIds)
                .getResultList();
    }
}