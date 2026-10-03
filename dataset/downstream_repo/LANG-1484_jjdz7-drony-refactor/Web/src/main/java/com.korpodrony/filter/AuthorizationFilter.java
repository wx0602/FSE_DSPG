package com.korpodrony.filter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.*;
import javax.servlet.annotation.WebFilter;
import javax.servlet.annotation.WebInitParam;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebFilter(
        filterName = "AuthorizationFilter",
        urlPatterns = {"/*"},
        initParams = {
                @WebInitParam(name = "userType", value = "GUEST"),
        }
)
public class AuthorizationFilter implements Filter {

    public static final String REDIRECT_LOGIN = "/login";
    public static final String USER_PATH = "/user";
    public static final String ADMIN_PATH = "/admin";
    public static final String ADMIN_USER_TYPE = "ADMIN";
    public static final String SUPER_ADMIN_USER_TYPE = "SUPER_ADMIN";
    public static final String GUEST_USER_TYPE = "GUEST";

    private static final Logger logger = LoggerFactory.getLogger("com.korpodrony.oauth");

    private String userType;
    private String defaultUserType;

    @Override
    public void init(FilterConfig filterConfig) {
        defaultUserType = filterConfig.getInitParameter("userType");
    }

    @Override
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse,
                         FilterChain filterChain) throws IOException, ServletException {
        resetUserTypeToDefaultValue();
        HttpServletRequest req = (HttpServletRequest) servletRequest;
        HttpServletResponse resp = (HttpServletResponse) servletResponse;
        String path = setPath(req);
        setUserType(req);
        authorizeAdmin(resp, path);
        authorizeUser(resp, path);
        filterChain.doFilter(servletRequest, servletResponse);
    }

    private void resetUserTypeToDefaultValue() {
        userType = defaultUserType;
    }

    private String setPath(HttpServletRequest req) {
        String path = req.getServletPath();
        logger.info("Trying to log to path: " + path);
        return path;
    }

    private void setUserType(HttpServletRequest req) {
        String sessionUserType = (String) req.getSession().getAttribute("userType");
        logger.info("userType: ", sessionUserType);
        if (checkIfSessionUserTypeExists(sessionUserType)) {
            userType = sessionUserType;
        }
    }

    private boolean checkIfSessionUserTypeExists(String sessionUserType) {
        return !(sessionUserType == null || sessionUserType.isEmpty());
    }

    private void authorizeAdmin(HttpServletResponse resp, String path) throws IOException {
        if ((path.startsWith(ADMIN_PATH)) && checkIfUserHasAccessToAdminPart()) {
            resp.sendRedirect(REDIRECT_LOGIN);
            logger.warn("An unauthorized attempt to recipe edition panel has occurred!");
        }
    }

    private boolean checkIfUserHasAccessToAdminPart() {
        return !userType.equals(ADMIN_USER_TYPE) && !userType.equals(SUPER_ADMIN_USER_TYPE);
    }

    private void authorizeUser(HttpServletResponse resp, String path) throws IOException {
        if ((path.startsWith(USER_PATH)) && (userType.equals(GUEST_USER_TYPE))) {
            resp.sendRedirect(REDIRECT_LOGIN);
            logger.warn("An unauthorized attempt to the admin panel has occurred!");
        }
    }
}
