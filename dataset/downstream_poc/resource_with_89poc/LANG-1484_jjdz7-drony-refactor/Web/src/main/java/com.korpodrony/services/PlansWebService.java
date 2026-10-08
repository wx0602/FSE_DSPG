package com.korpodrony.services;

import com.korpodrony.daoInterfaces.PlanRepositoryDaoInterface;
import com.korpodrony.dto.PlanDTO;
import com.korpodrony.dto.SimplifiedActivityDTO;
import com.korpodrony.dto.SimplifiedPlanDTO;
import com.korpodrony.entity.PlanEntity;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.inject.Inject;
import java.util.List;
import java.util.stream.Collectors;

@RequestScoped
public class PlansWebService {

    @EJB
    PlanRepositoryDaoInterface planRepositoryDao;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.services");

    public List<SimplifiedPlanDTO> getAllPlans() {
        logger.debug("getAllSimplifiedPlansDTO called");
        return planRepositoryDao.getAllSimplifiedPlansDTO();
    }

    public boolean hasPlan(int planId) {
        logger.debug("hasPlanWithThisID called");
        return planRepositoryDao.hasPlanWithThisID(planId);
    }

    public PlanDTO getPlanDTO(int id) {
        logger.debug("getPlanDTO called");
        return planRepositoryDao.getPlanDTO(id);
    }

    public boolean deletePlan(int planId) {
        logger.debug("deletePlan called");
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.PLANS, Action.DELETE);
        return planRepositoryDao.deletePlan(planId);
    }

    public List<SimplifiedActivityDTO> getAvailableActivities(int planId) {
        logger.debug("getAvailableActivities called");
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.PLANS, Action.GET_AVAILABLE_LIST);
        return planRepositoryDao.getAvailableSimplifiedActivitiesDTO(planId);
    }

    public boolean assignActivitiesToPlan(List<Integer> activitiesIds, int planId) {
        PlanEntity planEntity = planRepositoryDao.getPlanEntityWithRelations(planId);
        logger.debug("PlanEntity: " + planEntity + ", activtiesIds: " + activitiesIds);
        if (planEntity != null && activitiesIds != null) {
            planEntity.getAssignedActivities()
                    .addAll(planRepositoryDao
                            .getActivitiesEntitiesList(activitiesIds)
                    );
            planRepositoryDao.updatePlan(planEntity);
            return true;
        }
        return false;
    }

    public boolean unassignActivitiesFromPlan(List<Integer> activitiesIds, int planId) {
        PlanEntity planEntity = planRepositoryDao.getPlanEntityWithRelations(planId);
        logger.debug("PlanEntity: " + planEntity + ", activtiesIds: " + activitiesIds);
        if (planEntity != null) {
            if (checkIfAssignedActivitiesOrIdsToAssignAreNotNull(activitiesIds, planEntity)) {
                return false;
            }
            planEntity.setAssignedActivities(planEntity.getAssignedActivities()
                    .stream()
                    .filter(x -> !activitiesIds.contains(x.getId()))
                    .collect(Collectors.toSet())
            );
            planRepositoryDao.updatePlan(planEntity);
            return true;
        }
        return false;
    }

    public boolean editPlan(int planId, String name) {
        logger.debug("editPlan called");
        PlanEntity planEntity = planRepositoryDao.getPlanEntity(planId);
        if (planEntity == null) {
            return false;
        }
        planEntity.setName(name);
        planRepositoryDao.updatePlan(planEntity);
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.PLANS, Action.EDIT);
        return true;
    }

    public int createPlan(String name) {
        PlanEntity planEntity = new PlanEntity();
        planEntity.setName(name);
        logger.debug("createPlan called");
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.PLANS, Action.ADD);
        return planRepositoryDao.createPlan(planEntity);
    }

    private boolean checkIfAssignedActivitiesOrIdsToAssignAreNotNull(List<Integer> activityIDs, PlanEntity planEntity) {
        return planEntity.getAssignedActivities() == null || activityIDs == null;
    }
}