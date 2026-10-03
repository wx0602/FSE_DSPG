package com.korpodrony.dao;

import com.korpodrony.daoInterfaces.PlanRepositoryDaoInterface;
import com.korpodrony.dto.PlanDTO;
import com.korpodrony.dto.SimplifiedActivityDTO;
import com.korpodrony.dto.SimplifiedPlanDTO;
import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.entity.PlanEntity;
import org.hibernate.Hibernate;
import org.hibernate.proxy.HibernateProxy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;
import java.util.List;

@Stateless
public class PlanDaoImpl implements PlanRepositoryDaoInterface {

    @PersistenceContext(unitName = "korpodrony-hibernate")
    private EntityManager entityManager;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.dao");

    @Override
    public int createPlan(PlanEntity planEntity) {
        PlanEntity newPlanEntity = new PlanEntity();
        newPlanEntity.setName(planEntity.getName());
        entityManager.persist(newPlanEntity);
        logger.info("Created plan: " + planEntity + "from planEntity: " + planEntity);
        return newPlanEntity.getId();
    }

    @Override
    public boolean deletePlan(int planID) {
        if (hasPlanWithThisID(planID)) {
            entityManager.createQuery("DELETE FROM Plan p WHERE p.id=:id")
                    .setParameter("id", planID)
                    .executeUpdate();
            entityManager.flush();
            entityManager.clear();
            logger.info("Plan with id: " + planID + "has been removed");
            return true;
        } else {
            logger.info("Plan with id: " + planID + "doesn't exist");
            return false;
        }
    }

    @Override
    public void updatePlan(PlanEntity planEntity) {
        entityManager.merge(planEntity);
        logger.debug("Plan after changes: " + planEntity);
    }

    public List<SimplifiedPlanDTO> getAllSimplifiedPlansDTO() {
        logger.debug("Getting simplified list of plans");
        return entityManager
                .createQuery("SELECT new com.korpodrony.dto.SimplifiedPlanDTO(p.id, p.name) " +
                        "FROM Plan p", SimplifiedPlanDTO.class)
                .getResultList();
    }

    public List<SimplifiedPlanDTO> getAllSimplifiedPlansDTO(String name) {
        logger.debug("Getting simplified plans by name: " + name);
        return entityManager
                .createQuery("SELECT new com.korpodrony.dto.SimplifiedPlanDTO(p.id, p.name) " +
                        "FROM Plan p WHERE lower(p.name) like :name", SimplifiedPlanDTO.class)
                .setParameter("name", "%" + name + "%")
                .getResultList();
    }

    @Override
    public List<SimplifiedActivityDTO> getAvailableSimplifiedActivitiesDTO(int planId) {
        logger.debug("Getting available simplified ActivitiesDTOs for plan with id: " + planId);
        return entityManager.createQuery("SELECT new com.korpodrony.dto.SimplifiedActivityDTO(a.id, a.name, a.activitiesType)" +
                " from Activity a WHERE a NOT IN (select a from Plan p join p.assignedActivities a where p.id=:id)", SimplifiedActivityDTO.class)
                .setParameter("id", planId)
                .getResultList();
    }

    @Override
    public PlanDTO getPlanDTO(int planId) {
        logger.debug("Getting plan dto for id: " + planId);
        return getPlanEntity(planId).createPlanDTO();
    }

    @Override
    public boolean hasPlanWithThisID(int planID) {
        try {
            Object id = entityManager
                    .createQuery("SELECT p.id FROM Plan p where p.id=:id")
                    .setParameter("id", planID)
                    .getSingleResult();
            logger.debug("Has plan with id: " + planID);
            return true;
        } catch (NoResultException e) {
            logger.info("Doesn't have plan with id: " + planID);
            return false;
        }
    }

    public PlanEntity getPlanEntity(int planId) {
        logger.debug("Getting planEntity for id: " + planId);
        return entityManager.find(PlanEntity.class, planId);
    }

    public PlanEntity getPlanEntityWithRelations(int planId) {
        logger.debug("Getting planEntity for id: " + planId);
        PlanEntity planEntity = entityManager.find(PlanEntity.class, planId);
        Hibernate.initialize(planEntity.getAssignedActivities());
        return planEntity;
    }

    public List<ActivityEntity> getActivitiesEntitiesList(List<Integer> activitiesIds) {
        List<ActivityEntity> activities = entityManager.createQuery("SELECT a from Activity a WHERE a.id in (:activtiesIds)", ActivityEntity.class)
                .setParameter("activtiesIds", activitiesIds)
                .getResultList();
        activities.forEach(x->Hibernate.initialize(x.getAssigned_users()));
        return activities;
    }

    @Override
    public boolean unassignActivityFromPlan(int activityId, int planId) {
        ActivityEntity activityEntity = getActivityEntity(activityId);
        logger.debug("ActivityEntity: " + activityEntity);
        PlanEntity planEntity = getPlanEntity(planId);
        if (activityEntity != null && planEntity != null) {
            if (planEntity.getAssignedActivities() == null) {
                return false;
            }
            boolean result = planEntity.getAssignedActivities()
                    .remove(activityEntity);
            entityManager.merge(planEntity);
            logger.debug("Activity unassigned from Plan: " + result);
            return result;
        }
        return false;
    }

    public ActivityEntity getActivityEntity(int activityId) {
        logger.debug("Getting activityEntity for id: " + activityId);
        return entityManager.find(ActivityEntity.class, activityId);
    }
}
