package com.korpodrony.servlet.admin;

import com.korpodrony.dto.ActivityDTO;
import com.korpodrony.freemarker.TemplateProvider;
import com.korpodrony.services.ActivitiesWebService;
import com.korpodrony.validation.Validator;
import freemarker.template.Template;
import freemarker.template.TemplateException;

import javax.inject.Inject;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@WebServlet(urlPatterns = {"admin/activity", "admin/activity-unassign", "admin/activity-assign", "admin/activity-add"})
public class ActivityServlet extends HttpServlet {

    @Inject
    TemplateProvider templateProvider;

    @Inject
    ActivitiesWebService activitiesWebService;

    @Inject
    Validator validator;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        PrintWriter writer = resp.getWriter();
        String url = req.getServletPath();
        switch (url) {
            case "/admin/activity": {
                String requestedId = req.getParameter("id");
                if (setRespStatusOnValidationFailure(resp, validator.validateIntegerAsPositiveValue(requestedId))) {
                    break;
                }
                int id = Integer.parseInt(requestedId);
                if (setRespStatusOnValidationFailure(resp, activitiesWebService.hasActivity(id))) {
                    break;
                }
                Map<String, Object> model = getActivityModel(id);
                processTemplate(writer, model, templateProvider.ACTIVITY_TEMPLATE);
                break;
            }
            case "/admin/activity-add": {
                processTemplate(writer, null, templateProvider.ADD_ACTIVITY_TEMPLATE);
                break;
            }
            default: {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
            }
        }
    }

    @Override
    protected void doPut(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        PrintWriter writer = resp.getWriter();
        String url = req.getServletPath();
        switch (url) {
            case "/admin/activity-assign": {
                setRespStatusOnValidationFailure(resp, assignUserToActivity(req.getParameterMap()));
                break;
            }
            case "/admin/activity-unassign": {
                setRespStatusOnValidationFailure(resp, unassignUserToActivity(req.getParameterMap()));
                break;
            }
            case "/admin/activity": {
                setRespStatusOnValidationFailure(resp, editActivity(req.getParameterMap()));
                break;
            }
            default: {
                resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            }
        }
    }

    @Override
    protected void doDelete(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (!req.getServletPath().equals("/admin/activity")) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return;
        }
        String requestedId = req.getParameter("id");
        if (setRespStatusOnValidationFailure(resp, requestedId)) {
            return;
        }
        int id = Integer.parseInt(requestedId);
        if (setRespStatusOnValidationFailure(resp, activitiesWebService.hasActivity(id))) {
            return;
        }
        if (activitiesWebService.deleteActivity(id)) {
            return;
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (req.getServletPath().equals("/admin/activity")) {
            if (setRespStatusOnValidationFailure(resp, createActivity(req.getParameterMap()))) {
                return;
            }
        } else {
            resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    private boolean setRespStatusOnValidationFailure(HttpServletResponse resp, boolean statement) {
        if (!statement) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return true;
        }
        return false;
    }

    private boolean setRespStatusOnValidationFailure(HttpServletResponse resp, String requestedId) {
        if (!validator.validateIntegerAsPositiveValue(requestedId)) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return true;
        }
        return false;
    }

    private Map<String, Object> getActivityModel(int id) {
        ActivityDTO activityDTO = activitiesWebService.getActivityDTO(id);
        Map<String, Object> model = new HashMap<>();
        model.put("activity", activityDTO);
        model.put("users", activityDTO.getAssignedUsers());
        model.put("availableUsers", activitiesWebService.getAvailableUserDTO(id));
        return model;
    }

    private void processTemplate(PrintWriter writer, Map<String, Object> model, String path) throws IOException {
        Template template = templateProvider.getTemplate(getServletContext(), path);
        try {
            template.process(model, writer);
            return;
        } catch (TemplateException e) {
            return;
        }
    }

    private boolean assignUserToActivity(Map<String, String[]> parameterMap) {
        if (checkAssignParameters(parameterMap)) {
            int activityId = Integer.parseInt(parameterMap.get("id")[0]);
            List<Integer> userIds = Arrays.stream(parameterMap.get("userid")[0]
                    .split(","))
                    .map(Integer::parseInt)
                    .collect(Collectors.toList());
            activitiesWebService.assignUsersToActivity(userIds, activityId);
            return true;
        } else {
            return false;
        }
    }

    private boolean checkAssignParameters(Map<String, String[]> parameterMap) {
        return checkParameters(parameterMap, 2, validateAssignParameters(parameterMap));
    }

    private boolean checkParameters(Map<String, String[]> parameterMap, int number, boolean statement) {
        return checkNumberOfParameters(number, countParameters(parameterMap)) && statement;
    }

    private boolean checkNumberOfParameters(int number, long l) {
        return l == number;
    }

    private long countParameters(Map<String, String[]> parameterMap) {
        return parameterMap.values()
                .stream()
                .map(x -> x.length)
                .filter(x -> checkNumberOfParameters(1, x))
                .count();
    }

    private boolean validateAssignParameters(Map<String, String[]> parameterMap) {
        String activityId = parameterMap.get("id")[0];
        String activityUserId = parameterMap.get("userid")[0];
        boolean result = Arrays.stream(activityUserId
                .split(","))
                .map(x -> validator.validateIntegerAsPositiveValue(x))
                .allMatch(x -> x);
        return validator.validateIntegerAsPositiveValue(activityId) && result;
    }

    private boolean unassignUserToActivity(Map<String, String[]> parameterMap) {
        if (checkUnassignParmeters(parameterMap)) {
            int activityId = Integer.parseInt(parameterMap.get("id")[0]);
            List<Integer> userIds = Arrays.stream(parameterMap.get("userid")[0]
                    .split(","))
                    .map(Integer::parseInt)
                    .collect(Collectors.toList());
            activitiesWebService.unassignUsersFromActivity(userIds, activityId);
            return true;
        } else {
            return false;
        }
    }

    private boolean checkUnassignParmeters(Map<String, String[]> parameterMap) {
        return checkParameters(parameterMap, 2, validateAssignParameters(parameterMap));
    }

    private boolean editActivity(Map<String, String[]> parameterMap) {
        if (checkEditParameters(parameterMap)) {
            int activityId = Integer.parseInt(parameterMap.get("id")[0]);
            String name = parameterMap.get("name")[0].trim();
            short maxUsers = Short.parseShort(parameterMap.get("maxusers")[0]);
            byte duration = Byte.parseByte(parameterMap.get("duration")[0]);
            int activityType = Integer.parseInt(parameterMap.get("activitytype")[0]);
            return activitiesWebService.editActivity(activityId, name, maxUsers, duration, activityType);
        } else {
            return false;
        }
    }

    private boolean checkEditParameters(Map<String, String[]> parameterMap) {
        return checkParameters(parameterMap, 5, validateEditParameters(parameterMap));
    }

    private boolean validateEditParameters(Map<String, String[]> parameterMap) {
        String activityId = parameterMap.get("id")[0];
        String name = parameterMap.get("name")[0];
        String maxUsers = parameterMap.get("maxusers")[0];
        String duration = parameterMap.get("duration")[0];
        String activityType = parameterMap.get("activitytype")[0];
        return validator.validateIntegerAsPositiveValue(activityId)
                && validator.validateString(name)
                && validator.validateShort(maxUsers)
                && validator.validateByte(duration)
                && validator.validateActivityTypeInteger(activityType);
    }

    private boolean createActivity(Map<String, String[]> parameterMap) {
        if (checkParameters(parameterMap, 4, validateCreateParameters(parameterMap))) {
            String name = parameterMap.get("name")[0].trim();
            short maxUsers = Short.parseShort(parameterMap.get("maxusers")[0]);
            byte duration = Byte.parseByte(parameterMap.get("duration")[0]);
            int activityType = Integer.parseInt(parameterMap.get("activitytype")[0]);
            activitiesWebService.createActivity(name, maxUsers, duration, activityType);
            return true;
        }
        return false;
    }

    private boolean validateCreateParameters(Map<String, String[]> parameterMap) {
        String name = parameterMap.get("name")[0];
        String maxUsers = parameterMap.get("maxusers")[0];
        String duration = parameterMap.get("duration")[0];
        String activityType = parameterMap.get("activitytype")[0];
        return validator.validateString(name)
                && validator.validateShort(maxUsers)
                && validator.validateByte(duration)
                && validator.validateActivityTypeInteger(activityType);
    }
}