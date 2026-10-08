package com.korpodrony.rest;

import com.korpodrony.reports.dto.ReportsStatisticDTO;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;

import javax.ejb.Local;
import java.util.List;

@Local
public interface ReportsStatisticsRestConsumerInterface {

    void createReportsStatisticsEntry(View view, Action action);

    List<ReportsStatisticDTO> getAllReportsStatistics();

}
