package com.korpodrony.oauth;

import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.inject.Inject;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.IOException;

@WebServlet("/logout")
public class LogoutServlet extends HttpServlet {

    private static final Logger logger = LoggerFactory.getLogger("com.korpodrony.oauth");
    private static final String USER_ID_ATTR = GoogleLoginCallbackServlet.USER_ID_ATTR;
    private static final String REDIRECT = GoogleLoginCallbackServlet.REDIRECT;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    protected void doGet(HttpServletRequest req, HttpServletResponse resp) {

        resp.setCharacterEncoding("UTF-8");

        HttpSession session = req.getSession();
        logUserLogOut(session);
        session.invalidate();
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.LOGGING, Action.LOGOUT);
        try {
            resp.sendRedirect(REDIRECT);
        } catch (IOException e) {
            logger.error(e.getMessage());
        }
    }

    private void logUserLogOut(HttpSession session) {
        Object userId = session.getAttribute(USER_ID_ATTR);
        if (userId != null) {
            logger.info("User " + (int) userId + " log out successfully");
        }
    }
}