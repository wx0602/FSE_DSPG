package com.korpodrony.servlet.admin;

import com.korpodrony.freemarker.TemplateProvider;
import com.korpodrony.services.SearchWebService;
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

@WebServlet(urlPatterns = {"admin/search", "admin/search-users", "admin/search-activities", "admin/search-plans"})
public class SearchServlet extends HttpServlet {

    @Inject
    TemplateProvider templateProvider;

    @Inject
    SearchWebService searchWebService;

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("text/html;charset=UTF-8");
        PrintWriter writer = resp.getWriter();
        String url = req.getServletPath();
        switch (url) {
            case "/admin/search": {
                Template template = templateProvider.getTemplate(getServletContext(), TemplateProvider.SEARCH_TEMPLATE);
                try {
                    template.process(null, writer);
                    break;
                } catch (TemplateException e) {
                }
            }
            case "/admin/search-users": {
                String name = getSearchText(req, resp);
                writer.print(searchWebService.getUsersByName(name));
                writer.flush();
                break;
            }
            case "/admin/search-activities": {
                String name = getSearchText(req, resp);
                writer.print(searchWebService.getActivitiesByName(name));
                writer.flush();
                break;
            }
            case "/admin/search-plans": {
                String name = getSearchText(req, resp);
                writer.print(searchWebService.getPlansByName(name));
                writer.flush();
                break;
            }
            default: {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
            }
        }
    }

    private String getSearchText(HttpServletRequest req, HttpServletResponse resp) {
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        return req.getParameter("name").toLowerCase();
    }
}
