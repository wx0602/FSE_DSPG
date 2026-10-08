package com.korpodrony.daoInterfaces;

import com.korpodrony.dto.PlanDTO;
import com.korpodrony.dto.SimplifiedActivityDTO;
import com.korpodrony.dto.SimplifiedPlanDTO;
import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.entity.PlanEntity;

import javax.ejb.Local;
import java.util.List;

@Local
public interface PlanRepositoryDaoInterface {

    int createPlan(PlanEntity planEntity);

    boolean deletePlan(int planID);

    void updatePlan(PlanEntity planEntity);

    List<SimplifiedPlanDTO> getAllSimplifiedPlansDTO();

    List<SimplifiedPlanDTO> getAllSimplifiedPlansDTO(String name);

    List<SimplifiedActivityDTO> getAvailableSimplifiedActivitiesDTO(int planId);

    PlanDTO getPlanDTO(int planId);

    boolean hasPlanWithThisID(int planID);

    ActivityEntity getActivityEntity(int activityId);

    PlanEntity getPlanEntity(int planId);

    PlanEntity getPlanEntityWithRelations(int planId);

    List<ActivityEntity> getActivitiesEntitiesList(List<Integer> activitiesIds);

    boolean unassignActivityFromPlan(int activityId, int planId);
}