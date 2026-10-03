package com.korpodrony.daoInterfaces;

import com.korpodrony.dto.ActivityDTO;
import com.korpodrony.dto.SimplifiedActivityDTO;
import com.korpodrony.dto.UserDTO;
import com.korpodrony.entity.ActivityEntity;
import com.korpodrony.entity.UserEntity;
import com.korpodrony.model.ActivitiesType;

import javax.ejb.Local;
import java.util.List;

@Local
public interface ActivityRepositoryDaoInterface {

    int createActivity(ActivityEntity activity);

    void updateActivity(ActivityEntity activityEntity);

    boolean deleteActivity(int activityID);

    boolean hasActivityWithThisID(int activityID);

    List<SimplifiedActivityDTO> getAllSimplifiedActivates();

    List<SimplifiedActivityDTO> getAllUserSimplifiedActivates(int userId);

    List<SimplifiedActivityDTO> getAllSimplifiedActivates(ActivitiesType activitiesType);

    ActivityEntity getActivityEntity(int activityId);

    ActivityEntity getActivityEntityWithRelations(int activityId);

    ActivityDTO getActivityDTO(int activityId);

    List<UserDTO> getAvailableUsersDTO(int activityId);

    List<UserEntity> getUsersEntitiesList(List<Integer> usersIds);

    List<SimplifiedActivityDTO> getAllSimplifiedActivates(String name);
}