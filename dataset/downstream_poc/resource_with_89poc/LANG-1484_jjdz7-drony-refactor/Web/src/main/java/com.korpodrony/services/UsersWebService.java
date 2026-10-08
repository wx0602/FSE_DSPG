package com.korpodrony.services;

import com.korpodrony.daoInterfaces.UserRepositoryDaoInterface;
import com.korpodrony.dto.AuthUserDTO;
import com.korpodrony.dto.UserDTO;
import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.entity.UserEntity;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.inject.Inject;
import java.util.List;

@RequestScoped
public class UsersWebService {

    @EJB
    UserRepositoryDaoInterface userRepositoryDao;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    @Inject
    CurrentUserService currentUserService;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.services");

    public List<UserDTO> getAllUsers() {
        logger.debug("getAllUsers called");
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.USERS, Action.GET_AVAILABLE_LIST);
        return userRepositoryDao.getAllUsers();
    }

    public List<UserEntity> getAllUserEntities() {
        logger.debug("getAllUsers called");
        return userRepositoryDao.getAllUsersEntities();
    }

    public int findUserIdByEmail(String email) {
        if (email == null) {
            throw new IllegalArgumentException("Email cannot be null");
        }
        return userRepositoryDao.getUserIdByEmail(email);
    }

    public int createUser(UserEntity userEntity) {
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.USERS, Action.ADD);
        return userRepositoryDao.createUser(userEntity);
    }

    public void updatePermissionLevel(int userId, PermissionLevel level) {
        if (level == null) {
            throw new IllegalArgumentException("PermissionLevel cannot be null");
        }
        UserEntity userEntity = userRepositoryDao.getUserEntity(userId);
        userEntity.setPermissionLevel(level);
        userRepositoryDao.updateUser(userEntity);
    }

    public AuthUserDTO findAuthUserDTOByEmail(String email) {
        currentUserService.setEmail(email);
        return userRepositoryDao.getAuthUserDTO(email);
    }
}