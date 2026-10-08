package com.korpodrony.reports.interfaces;

import com.korpodrony.reports.dto.ReportsStatisticDTO;

import javax.ejb.Local;
import java.util.List;

@Local
public interface ReportsStatisticsInterface {

    int createReportsStatisticsEntry(ReportsStatisticDTO reportsStatisticDTO);

    List<ReportsStatisticDTO> getAllReportsStatistics();

}
