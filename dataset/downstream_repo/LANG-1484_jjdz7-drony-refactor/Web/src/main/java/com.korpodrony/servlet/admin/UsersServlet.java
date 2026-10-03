package com.korpodrony.servlet.admin;

import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.freemarker.TemplateProvider;
import com.korpodrony.services.UsersWebService;
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

@WebServlet("admin/users")
public class UsersServlet extends HttpServlet {

    @Inject
    TemplateProvider templateProvider;

    @Inject
    UsersWebService usersWebService;

    @Inject
    Validator validator;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        PrintWriter writer = resp.getWriter();
        String path = setPath(req, resp);
        Map<String, Object> model = getModel(path);
        Template template = templateProvider.getTemplate(getServletContext(), path);
        try {
            template.process(model, writer);
        } catch (TemplateException e) {
            e.printStackTrace();
        }
    }

    private Map<String, Object> getModel(String path) {
        Map<String, Object> model = new HashMap<>();
        if (templateProvider.SUPER_ADMIN_USERS_TEMPLATE.equals(path)) {
            model.put("users", usersWebService.getAllUserEntities());
        } else {
            model.put("users", usersWebService.getAllUsers());
        }
        return model;
    }

    @Override
    protected void doPut(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        String userType = req.getSession().getAttribute("userType").toString();
        if (checkPermissionLevelIsNotSuperAdmin(resp, userType)) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return;
        }
        String sessionUserId = req.getSession().getAttribute("userId").toString();
        if (checkUserSelfProtection(req, resp, sessionUserId)) {
            return;
        }
        if (validateParameters(req, resp)) {
            updatePermissionLevel(req);
            return;
        }
        resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
    }

    private String setPath(HttpServletRequest req, HttpServletResponse resp) {
        String userType = req.getSession().getAttribute("userType").toString();
        if (checkPermissionLevelIsNotSuperAdmin(resp, userType)) {
            return templateProvider.USERS_TEMPLATE;
        } else {
            return templateProvider.SUPER_ADMIN_USERS_TEMPLATE;
        }
    }

    private boolean checkPermissionLevelIsNotSuperAdmin(HttpServletResponse resp, String userType) {
        if (!PermissionLevel.SUPER_ADMIN.toString().equals(userType)) {
            return true;
        }
        return false;
    }

    private boolean checkUserSelfProtection(HttpServletRequest req, HttpServletResponse resp, String sessionUserId) {
        if (req.getParameter("id").equals(sessionUserId)) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return true;
        }
        return false;
    }

    private boolean validateParameters(HttpServletRequest req, HttpServletResponse resp) {
        if (!validateNumber(req, "id") || !validateString(req, "select")) {
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            return false;
        }
        return true;
    }

    private boolean validateNumber(HttpServletRequest req, String attribute) {
        return validator.validateInteger(req.getParameter(attribute));
    }

    private boolean validateString(HttpServletRequest req, String attribute) {
        return validator.validateString(req.getParameter(attribute));
    }

    private PermissionLevel getPermissionLevelFromString(String value) {
        switch (value) {
            case "SUPER_ADMIN":
                return PermissionLevel.SUPER_ADMIN;
            case "ADMIN":
                return PermissionLevel.ADMIN;
            default:
                return PermissionLevel.USER;
        }
    }

    private void updatePermissionLevel(HttpServletRequest req) {
        int id = Integer.parseInt(req.getParameter("id"));
        String value = req.getParameter("select");
        PermissionLevel permissionLevel = getPermissionLevelFromString(value);
        usersWebService.updatePermissionLevel(id, permissionLevel);
    }
}