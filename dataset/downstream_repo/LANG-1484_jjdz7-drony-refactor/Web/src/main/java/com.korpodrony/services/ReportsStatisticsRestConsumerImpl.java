package com.korpodrony.services;

import com.korpodrony.reports.client.ReportsConstants;
import com.korpodrony.reports.dto.LocalDateTimeConverter;
import com.korpodrony.reports.dto.ReportsStatisticDTO;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import org.glassfish.jersey.jackson.JacksonFeature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.Stateless;
import javax.inject.Inject;
import javax.ws.rs.client.Client;
import javax.ws.rs.client.ClientBuilder;
import javax.ws.rs.client.Entity;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Collections;
import java.util.List;

@Stateless
public class ReportsStatisticsRestConsumerImpl implements ReportsStatisticsRestConsumerInterface {

    private Logger logger = LoggerFactory.getLogger(ReportsStatisticsRestConsumerImpl.class);

    @Inject
    CurrentUserService currentUserService;

    @Override
    public void createReportsStatisticsEntry(View view, Action action) {

        String email = currentUserService.getEmail();
        if (email == null) {
            logger.error("User not logged. Statistics not added.");
            return;
        }

        Client client = ClientBuilder.newClient().register(new JacksonFeature());

        ReportsStatisticDTO reportStatisticsDto = createReportStatisticsDTO(view, action, email);

        Response response = client
                .target(ReportsConstants.URL)
                .path(ReportsConstants.CREATE_ENTRY_ENDPOINT)
                .request(MediaType.APPLICATION_JSON)
                .post(Entity.entity(reportStatisticsDto, MediaType.APPLICATION_JSON));

        int status = response.getStatus();
        if (status != Response.Status.CREATED.getStatusCode()) {
            String s = response.readEntity(String.class);
            logger.error("ERROR! {} ", s);

        }

        logger.info("created reports statistics status: {} entry: {} ", status, reportStatisticsDto);
    }

    private ReportsStatisticDTO createReportStatisticsDTO(View view, Action action, String email) {


        ReportsStatisticDTO reportsStatisticDTO = new ReportsStatisticDTO();
        reportsStatisticDTO.setAction(action);
        reportsStatisticDTO.setEmail(email);
        reportsStatisticDTO.setView(view);

        LocalDateTime currentTime = LocalDateTime.now(ZoneId.systemDefault());
        String localDateTimeString = LocalDateTimeConverter.fromLocalDateTime(currentTime);
        reportsStatisticDTO.setTimeOfAction(localDateTimeString);

        return reportsStatisticDTO;
    }

    @Override
    public List<ReportsStatisticDTO> getAllReportsStatistics() {
        logger.debug("Getting list of all statistics");

        // TODO must be implemented

        return Collections.emptyList();
    }

}
