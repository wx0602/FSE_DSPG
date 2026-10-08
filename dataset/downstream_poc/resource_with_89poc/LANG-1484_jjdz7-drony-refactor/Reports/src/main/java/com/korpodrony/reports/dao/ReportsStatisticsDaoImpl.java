package com.korpodrony.reports.dao;

import com.korpodrony.reports.dto.LocalDateTimeConverter;
import com.korpodrony.reports.dto.ReportsStatisticDTO;
import com.korpodrony.reports.entity.ReportsStatisticsEntity;
import com.korpodrony.reports.interfaces.ReportsStatisticsInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ejb.Stateless;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import java.time.LocalDateTime;
import java.util.List;

@Stateless
public class ReportsStatisticsDaoImpl implements ReportsStatisticsInterface {

    private Logger logger = LoggerFactory.getLogger(ReportsStatisticsDaoImpl.class);

    @PersistenceContext(unitName = "korpodrony-hibernate-reports")
    private EntityManager entityManager;

    @Override
    public int createReportsStatisticsEntry(ReportsStatisticDTO reportsStatisticDTO) {

        ReportsStatisticsEntity reportsStatistics = new ReportsStatisticsEntity();
        reportsStatistics.setEmail(reportsStatisticDTO.getEmail());
        reportsStatistics.setView(reportsStatisticDTO.getView());
        reportsStatistics.setAction(reportsStatisticDTO.getAction());

        String timeOfAction = reportsStatisticDTO.getTimeOfAction();
        LocalDateTime localDateTime = LocalDateTimeConverter.fromStringToLocalDateTime(timeOfAction);
        reportsStatistics.setTimeOfAction(localDateTime);

        entityManager.persist(reportsStatistics);
        entityManager.flush();
        logger.info("created reports statistics: {} ", reportsStatistics);
        return reportsStatistics.getId();
    }

    @Override
    public List<ReportsStatisticDTO> getAllReportsStatistics() {

        logger.debug("Getting list of ReportsStatisticDTO");
          return entityManager
                .createQuery("SELECT new com.korpodrony.reports.dto.ReportsStatisticDTO(r.id, r.email, r.view, r.action, r.timeOfAction) FROM ReportsStatistics r", ReportsStatisticDTO.class)
                .getResultList();
    }
}
