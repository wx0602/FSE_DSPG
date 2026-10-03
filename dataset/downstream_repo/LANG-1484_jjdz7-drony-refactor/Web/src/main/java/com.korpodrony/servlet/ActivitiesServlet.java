package com.korpodrony.servlet;

import com.korpodrony.freemarker.TemplateProvider;
import com.korpodrony.model.ActivitiesType;
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
import java.util.HashMap;
import java.util.Map;

@WebServlet(urlPatterns = {"admin/activities", "user/activities", "user/useractivities"})
public class ActivitiesServlet extends HttpServlet {

    private final int LECTURE_ACTIVITY_TYPE_NUMBER = 1;
    private final int EXERCISE_ACTIVITY_TYPE_NUMBER = 2;
    private final int WORKSHOP_ACTIVITY_TYPE_NUMBER = 3;
    private final int ALL_ACTIVITIES_TYPES_NUMBER = 4;
    private final String ACTIVITIES_FIELD = "activities";
    private final String TYPE_FIELD = "type";

    @Inject
    TemplateProvider templateProvider;

    @Inject
    Validator validator;

    @Inject
    ActivitiesWebService activitiesWebService;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        PrintWriter writer = resp.getWriter();
        String typeNumber = req.getParameter(TYPE_FIELD);
        int userId = (Integer) req.getSession().getAttribute("userId");
        String url = req.getServletPath();
        Map<String, Object> model = new HashMap<>();
        switch (url) {
            case "/admin/activities": {
                model = getRegularModel(typeNumber);
                proccesTemplate(writer, model, templateProvider.ADMIN_ACTIVITIES_TEMPLATE);
                break;
            }
            case "/user/activities": {
                model = getRegularModel(typeNumber);
                proccesTemplate(writer, model, templateProvider.USER_ACTIVITIES_TEMPLATE);
                break;
            }
            case "/user/useractivities": {
                model = getUserActivitiesModel(typeNumber, userId);
                proccesTemplate(writer, model, templateProvider.USER_ASSIGNED_TO_ACTIVITIES_TEMPLATE);
            }
            default: {
                resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            }
        }
    }

    private Map<String, Object> getUserActivitiesModel(String typeNumber, int userId) {
        Map<String, Object> model = new HashMap<>();
        if (!validator.validateIntegerAsPositiveValue(typeNumber)) {
            model.put(ACTIVITIES_FIELD, activitiesWebService.getAllUserActivities(userId));
            model.put(TYPE_FIELD, ALL_ACTIVITIES_TYPES_NUMBER);
            return model;
        }
        addToModelTypeActivities(typeNumber, model);
        return model;
    }

    private Map<String, Object> getRegularModel(String typeNumber) {
        Map<String, Object> model = new HashMap<>();
        if (!validator.validateIntegerAsPositiveValue(typeNumber)) {
            model.put(ACTIVITIES_FIELD, activitiesWebService.getAllActivities());
            model.put(TYPE_FIELD, ALL_ACTIVITIES_TYPES_NUMBER);
            return model;
        }
        addToModelTypeActivities(typeNumber, model);
        return model;
    }

    private void addToModelTypeActivities(String typeNumber, Map<String, Object> model) {
        switch (Integer.parseInt(typeNumber)) {
            case 1: {
                putToModelActivitiesWithTypeNumber(model, LECTURE_ACTIVITY_TYPE_NUMBER);
                break;
            }
            case 2: {
                putToModelActivitiesWithTypeNumber(model, EXERCISE_ACTIVITY_TYPE_NUMBER);
                break;
            }
            case 3: {
                putToModelActivitiesWithTypeNumber(model, WORKSHOP_ACTIVITY_TYPE_NUMBER);
                break;
            }
            default: {
                putToModelActivitiesWithTypeNumber(model, ALL_ACTIVITIES_TYPES_NUMBER);
            }
        }
    }

    private void putToModelActivitiesWithTypeNumber(Map<String, Object> model, int typeNumber) {
        if (typeNumber == ALL_ACTIVITIES_TYPES_NUMBER) {
            model.put(ACTIVITIES_FIELD, activitiesWebService.
                    getAllActivities()
            );
        } else {
            model.put(ACTIVITIES_FIELD, activitiesWebService.
                    getAllActivitiesByActivityType(ActivitiesType.getActivity(typeNumber))
            );
        }
        model.put(TYPE_FIELD, typeNumber);
    }

    private void proccesTemplate(PrintWriter writer, Map<String, Object> model, String path) throws IOException {
        Template template = templateProvider.getTemplate(getServletContext(), path);
        try {
            template.process(model, writer);
            return;
        } catch (TemplateException e) {
            return;
        }
    }
}