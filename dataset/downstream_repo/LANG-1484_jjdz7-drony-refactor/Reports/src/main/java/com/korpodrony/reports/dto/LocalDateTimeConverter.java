package com.korpodrony.reports.dto;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class LocalDateTimeConverter {

    private static final String PATTERN = "yyyy-MM-dd HH:mm:ss";

    private static DateTimeFormatter formatter = DateTimeFormatter.ofPattern(PATTERN);

    public static LocalDateTime fromStringToLocalDateTime(String localDateTimeAsAString) {

        return LocalDateTime.parse(localDateTimeAsAString, formatter);
    }

    public static String fromLocalDateTime(LocalDateTime localDateTime) {

        if (localDateTime == null) {
            return null;
        }
        return localDateTime.format(formatter);
    }
}
