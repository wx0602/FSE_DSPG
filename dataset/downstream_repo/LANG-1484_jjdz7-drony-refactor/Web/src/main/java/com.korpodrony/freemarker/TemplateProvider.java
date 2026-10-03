package com.korpodrony.freemarker;

import freemarker.template.Configuration;
import freemarker.template.Template;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.enterprise.context.RequestScoped;
import javax.inject.Inject;
import javax.servlet.ServletContext;
import java.io.IOException;

@RequestScoped
public class TemplateProvider {

    public static final String ACTIVITY_TEMPLATE = "admin/activity.ftlh";
    public static final String ADD_ACTIVITY_TEMPLATE = "admin/activity-add.ftlh";
    public static final String ADD_PLAN_TEMPLATE = "admin/plan-add.ftlh";
    public static final String ADMIN_ACTIVITIES_TEMPLATE = "admin/activities.ftlh";
    public static final String USER_ACTIVITIES_TEMPLATE = "user/activities.ftlh";
    public static final String USER_ASSIGNED_TO_ACTIVITIES_TEMPLATE = "user/useractivities.ftlh";
    public static final String ADMIN_INDEX_TEMPLATE = "admin/adminIndex.ftlh";
    public static final String USER_INDEX_TEMPLATE = "userIndex.ftlh";
    public static final String GUEST_INDEX_TEMPLATE = "guestIndex.ftlh";
    public static final String UPLOAD_FILE_TEMPLATE = "admin/upload-file.ftlh";
    public static final String USERS_TEMPLATE = "admin/users.ftlh";
    public static final String SUPER_ADMIN_USERS_TEMPLATE = "superAdmin/users.ftlh";
    public static final String PLAN_TEMPLATE = "admin/plan.ftlh";
    public static final String PLANS_TEMPLATE = "admin/plans.ftlh";
    public static final String SEARCH_TEMPLATE = "admin/search.ftlh";
    public static final String ADMIN_PANEL = "admin/admin-panel.ftlh";
    private final String TEMPLATE_DIRECTORY_PATH = "WEB-INF/fm-templates";
    private Configuration configuration;

    @Inject
    private ConfigProvider configProvider;

    Logger logger = LoggerFactory.getLogger("com.korpodrony.freemarker");

    public Template getTemplate(ServletContext servletContext, String templateName) throws IOException {
        logger.debug("Getting template with name: " + templateName);
        configuration = configProvider.getConfiguration();
        configuration.setServletContextForTemplateLoading(servletContext, TEMPLATE_DIRECTORY_PATH);
        return configuration.getTemplate(templateName);
    }
}
