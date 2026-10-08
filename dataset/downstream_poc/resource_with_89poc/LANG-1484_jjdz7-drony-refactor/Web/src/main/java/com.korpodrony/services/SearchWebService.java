package com.korpodrony.services;

import com.korpodrony.daoInterfaces.ActivityRepositoryDaoInterface;
import com.korpodrony.daoInterfaces.PlanRepositoryDaoInterface;
import com.korpodrony.daoInterfaces.UserRepositoryDaoInterface;
import com.korpodrony.dto.UserDTO;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import com.korpodrony.utils.JSONWriter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.EJB;
import javax.enterprise.context.RequestScoped;
import javax.inject.Inject;
import java.util.List;

@RequestScoped
public class SearchWebService {

    @EJB
    PlanRepositoryDaoInterface planRepositoryDao;

    @EJB
    UserRepositoryDaoInterface userRepositoryDao;

    @EJB
    ActivityRepositoryDaoInterface activityRepositoryDao;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.services");

    public String getUsersByName(String name) {
        String[] credentials = name.split(" ");
        List<UserDTO> userDTObyName;
        logger.debug("Getting users by name: " + name);
        if (credentials.length == 1) {
            userDTObyName = userRepositoryDao.getUserDTObyName(credentials[0]);
        } else {
            userDTObyName = userRepositoryDao.getUserDTObyName(credentials[0], credentials[1]);
        }
        logger.debug("result: " + userDTObyName);
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.SEARCH, Action.GET_AVAILABLE_LIST);
        return JSONWriter.generateJsonString(
                userDTObyName
        );
    }

    public String getActivitiesByName(String name) {
        logger.debug("Getting activities by name: " + name);
        return JSONWriter.generateJsonString(activityRepositoryDao.getAllSimplifiedActivates(name)
        );
    }

    public String getPlansByName(String name) {
        logger.debug("Getting plans by name: " + name);
        return JSONWriter.generateJsonString(
                planRepositoryDao.getAllSimplifiedPlansDTO(name)
        );
    }
}