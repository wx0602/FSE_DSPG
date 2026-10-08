package com.korpodrony.servlet;

import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.freemarker.TemplateProvider;
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

@WebServlet("/index")
public class IndexServlet extends HttpServlet {

    @Inject
    TemplateProvider templateProvider;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        PrintWriter writer = resp.getWriter();
        String userType = (String) req.getSession().getAttribute("userType");
        String path = getPathToTemplate(userType);
        Template template = templateProvider.getTemplate(getServletContext(), path);
        try {
            template.process(null, writer);
        } catch (TemplateException e) {
            e.printStackTrace();
        }
    }

    private String getPathToTemplate(String userType) {
        if ((PermissionLevel.ADMIN.toString()).equals(userType) || (PermissionLevel.SUPER_ADMIN.toString()).equals(userType)) {
            return templateProvider.ADMIN_INDEX_TEMPLATE;
        } else if ((PermissionLevel.USER.toString()).equals(userType)) {
            return templateProvider.USER_INDEX_TEMPLATE;
        } else {
            return templateProvider.GUEST_INDEX_TEMPLATE;
        }
    }
}