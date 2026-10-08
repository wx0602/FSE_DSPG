package com.korpodrony.servlet.admin;

import com.korpodrony.dto.PlanDTO;
import com.korpodrony.freemarker.TemplateProvider;
import com.korpodrony.services.ActivitiesWebService;
import com.korpodrony.services.PlansWebService;
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
import java.util.*;
import java.util.stream.Collectors;

@WebServlet(urlPatterns = {"/admin/plan", "/admin/plan-unassign", "/admin/plan-assign", "/admin/plan-add"})
public class PlanServlet extends HttpServlet {

    @Inject
    TemplateProvider templateProvider;

    @Inject
    PlansWebService plansWebService;

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
            case "/admin/plan": {
                String requestedId = req.getParameter("id");
                if (setRespStatusOnValidationFailure(resp, validator.validateIntegerAsPositiveValue(requestedId))) {
                    break;
                }
                int id = Integer.parseInt(requestedId);
                if (setRespStatusOnValidationFailure(resp, plansWebService.hasPlan(id))) {
                    break;
                }
                Map<String, Object> model = getPlanModel(id);
                processTemplate(writer, model, templateProvider.PLAN_TEMPLATE);
                break;
            }
            case "/admin/plan-add": {
                Map<String, Object> model = getAddPlanModel();
                processTemplate(writer, model, templateProvider.ADD_PLAN_TEMPLATE);
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
            case "/admin/plan-assign": {
                if (setRespStatusOnValidationFailure(resp, assignActivityToPlan(req.getParameterMap()))) {
                    break;
                }
                setOKstatus(resp);
                break;
            }
            case "/admin/plan-unassign": {
                if (setRespStatusOnValidationFailure(resp, unassignActivityFromPlan(req.getParameterMap()))) {
                    break;
                }
                setOKstatus(resp);
                break;
            }
            case "/admin/plan": {
                if (setRespStatusOnValidationFailure(resp, editPlan(req.getParameterMap()))) {
                    break;
                }
                setOKstatus(resp);
                break;
            }
            default: {
                resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            }
        }
    }

    @Override
    protected void doDelete(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (!req.getServletPath().equals("/admin/plan")) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return;
        }
        String requestedId = req.getParameter("id");
        if (setRespStatusOnValidationFailure(resp, requestedId)) {
            return;
        }
        int id = Integer.parseInt(requestedId);
        if (setRespStatusOnValidationFailure(resp, plansWebService.hasPlan(id))) {
            return;
        }
        if (plansWebService.deletePlan(id)) {
            setOKstatus(resp);
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (req.getServletPath().equals("/admin/plan")) {
            if (setRespStatusOnValidationFailure(resp, createPlan(req.getParameterMap()))) {
                return;
            }
            setOKstatus(resp);
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

    private void setOKstatus(HttpServletResponse resp) {
        resp.setStatus(HttpServletResponse.SC_OK);
    }

    private Map<String, Object> getPlanModel(int id) {
        PlanDTO planDTO = plansWebService.getPlanDTO(id);
        Map<String, Object> model = new HashMap<>();
        model.put("plan", planDTO);
        model.put("activities", planDTO.getAssignedActivities());
        model.put("avaiableActivities", plansWebService.getAvailableActivities(id));
        return model;
    }

    private Map<String, Object> getAddPlanModel() {
        Map<String, Object> model = new HashMap<>();
        model.put("activities", activitiesWebService.getAllActivities());
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

    private boolean assignActivityToPlan(Map<String, String[]> parameterMap) {
        if (checkAssignParameters(parameterMap)) {
            int planId = Integer.parseInt(parameterMap.get("id")[0]);
            List<Integer> activityId = Arrays.stream(parameterMap.get("activityid")[0]
                    .split(","))
                    .map(Integer::parseInt)
                    .collect(Collectors.toList());
            return plansWebService.assignActivitiesToPlan(activityId, planId);
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
        String planId = parameterMap.get("id")[0];
        String activityIds = parameterMap.get("activityid")[0];
        boolean result = Arrays.stream(activityIds.split(","))
                .allMatch(x -> validator.validateIntegerAsPositiveValue(x));
        return validator.validateIntegerAsPositiveValue(planId) && result;
    }

    private boolean unassignActivityFromPlan(Map<String, String[]> parameterMap) {
        if (checkUnassignParmeters(parameterMap)) {
            int planId = Integer.parseInt(parameterMap.get("id")[0]);
            List<Integer> activitiesIds = Arrays.stream(parameterMap.get("activityid")[0]
                    .split(","))
                    .map(Integer::parseInt)
                    .collect(Collectors.toList());
            return plansWebService.unassignActivitiesFromPlan(activitiesIds, planId);
        } else {
            return false;
        }
    }

    private boolean checkUnassignParmeters(Map<String, String[]> parameterMap) {
        return checkParameters(parameterMap, 2, validateAssignParameters(parameterMap));
    }

    private boolean editPlan(Map<String, String[]> parameterMap) {
        if (checkEditParameters(parameterMap)) {
            int activityId = Integer.parseInt(parameterMap.get("id")[0]);
            String name = parameterMap.get("name")[0].trim();
            return plansWebService.editPlan(activityId, name);
        } else {
            return false;
        }
    }

    private boolean checkEditParameters(Map<String, String[]> parameterMap) {
        return checkParameters(parameterMap, 2, validateEditParameters(parameterMap));
    }

    private boolean validateEditParameters(Map<String, String[]> parameterMap) {
        String activityId = parameterMap.get("id")[0];
        String name = parameterMap.get("name")[0];
        return validator.validateIntegerAsPositiveValue(activityId)
                && validator.validateString(name);
    }

    private boolean createPlan(Map<String, String[]> parameterMap) {
        if (validateCreateParameters(parameterMap)) {
            String name = parameterMap.get("name")[0].trim();
            String activitiesIds = parameterMap.get("assignedactivities")[0].trim();
            int planId = plansWebService.createPlan(name);
            if (!activitiesIds.equals("")) {
                assignActivitiesToCreatedPlan(planId, parameterMap);
            }
            return true;
        }
        return false;
    }

    private boolean validateCreateParameters(Map<String, String[]> parameterMap) {
        String name = parameterMap.get("name")[0];
        String activitiesIds = parameterMap.get("assignedactivities")[0];
        boolean nameValidation = validator.validateString(name);
        if (activitiesIds.equals("")) {
            return nameValidation;
        }
        List<String> activitiesIdParam = getActivitiesParam(activitiesIds);
        boolean activitiesParamValidation = isActivitiesParamValid(activitiesIdParam);
        if (activitiesParamValidation) {
            boolean noRepeatsInActivitiesParam = isNoRepeatsInActivitiesParam(activitiesIdParam);
            boolean allActivitiesExists = doesAllActivitiesExists(activitiesIdParam);
            return nameValidation && noRepeatsInActivitiesParam && allActivitiesExists;
        }
        return false;
    }

    private List<String> getActivitiesParam(String activitiesIds) {
        return Arrays.stream(activitiesIds
                .split(","))
                .collect(Collectors.toList());
    }

    private boolean isActivitiesParamValid(List<String> activitiesIdParam) {
        return activitiesIdParam
                .stream()
                .allMatch(x -> validator.validateIntegerAsPositiveValue(x));
    }

    private boolean isNoRepeatsInActivitiesParam(List<String> activitiesIdParam) {
        return activitiesIdParam.stream().allMatch(new HashSet<>()::add);
    }

    private boolean doesAllActivitiesExists(List<String> activitiesIdParam) {
        return activitiesIdParam
                .stream().map(Integer::valueOf)
                .allMatch(x -> activitiesWebService.hasActivity(x));
    }

    private void assignActivitiesToCreatedPlan(int planId, Map<String, String[]> parameterMap) {
        List<Integer> activitiesToAssign = Arrays.stream(parameterMap.get("assignedactivities")[0]
                .split(","))
                .map(Integer::valueOf)
                .collect(Collectors.toList());
        plansWebService.assignActivitiesToPlan(activitiesToAssign, planId);
    }
}