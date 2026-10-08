package com.korpodrony.oauth;

import com.google.api.client.auth.oauth2.AuthorizationCodeFlow;
import com.google.api.client.auth.oauth2.AuthorizationCodeResponseUrl;
import com.google.api.client.auth.oauth2.Credential;
import com.google.api.client.extensions.servlet.auth.oauth2.AbstractAuthorizationCodeCallbackServlet;
import com.google.api.client.http.HttpRequestInitializer;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.services.oauth2.Oauth2;
import com.google.api.services.oauth2.model.Userinfoplus;
import com.google.auth.http.HttpCredentialsAdapter;
import com.google.auth.oauth2.AccessToken;
import com.google.auth.oauth2.GoogleCredentials;
import com.korpodrony.dto.AuthUserDTO;
import com.korpodrony.entity.UserEntity;
import com.korpodrony.entity.builder.UserEntityBuilder;
import com.korpodrony.reports.entity.Action;
import com.korpodrony.reports.entity.View;
import com.korpodrony.rest.ReportsStatisticsRestConsumerInterface;
import com.korpodrony.services.UsersWebService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.inject.Inject;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Date;
import java.util.UUID;

@WebServlet("/oauth2callback")
public class GoogleLoginCallbackServlet extends AbstractAuthorizationCodeCallbackServlet {

    private static final Logger logger = LoggerFactory.getLogger("com.korpodrony.oauth");
    private static final String APP_NAME = "Korpodrony";
    protected static final String USER_ID_ATTR = "userId";
    protected static final String USER_TYPE_ATTR = "userType";
    private static final String USER_TYPE_GUEST = "GUEST";
    protected static final String REDIRECT = "/index";
    @Inject
    private UsersWebService usersWebService;

    @Inject
    ReportsStatisticsRestConsumerInterface reportsStatisticsRestConsumerInterface;

    @Override
    protected void onSuccess(HttpServletRequest req, HttpServletResponse resp, Credential credential)
            throws IOException {
        AuthUserDTO verifiedUser = getAuthUserDTO(credential);
        setSessionAttributes(req, verifiedUser);
        setSessionAtrrUserType(req);
        resp.sendRedirect(REDIRECT);
        reportsStatisticsRestConsumerInterface.createReportsStatisticsEntry(View.LOGGING, Action.LOGIN);
    }

    @Override
    protected void onError(HttpServletRequest req, HttpServletResponse resp,
                           AuthorizationCodeResponseUrl errorResponse) {
        logger.error("Google auth error: " + errorResponse.getError());
    }

    @Override
    protected String getRedirectUri(HttpServletRequest req) {
        return GoogleLoginCommons.buildRedirectUri(req);
    }

    @Override
    protected AuthorizationCodeFlow initializeFlow() {
        return GoogleLoginCommons.buildFlow();
    }

    @Override
    protected String getUserId(HttpServletRequest req) {
        String randomUserId = UUID.randomUUID().toString();
        logger.info("getUserId: " + randomUserId);
        return randomUserId;
    }

    private AuthUserDTO getAuthUserDTO(Credential credential) throws IOException {
        GoogleCredentials googleCredentials = getCredentials(credential);
        HttpRequestInitializer requestInitializer = new HttpCredentialsAdapter(googleCredentials);
        Oauth2 oauth2 = getOauth2(requestInitializer);
        Userinfoplus userinfoplus = oauth2.userinfo().get().execute();
        return getVerifiedUser(userinfoplus);
    }

    private GoogleCredentials getCredentials(Credential credential) {
        AccessToken accessToken = new AccessToken(credential.getAccessToken(), new Date(credential.getExpirationTimeMilliseconds()));
        return GoogleCredentials.newBuilder()
                .setAccessToken(accessToken)
                .build();
    }

    private Oauth2 getOauth2(HttpRequestInitializer requestInitializer) {
        return new Oauth2.Builder(
                new NetHttpTransport(),
                JacksonFactory.getDefaultInstance(),
                requestInitializer).setApplicationName(APP_NAME).build();
    }

    private AuthUserDTO getVerifiedUser(Userinfoplus userinfoplus) {
        String email = userinfoplus.getEmail();
        if (usersWebService.findUserIdByEmail(email) == 0) {
            UserEntity user = UserEntityBuilder.anUserEntity()
                    .withEmail(email)
                    .withName(userinfoplus.getGivenName())
                    .withSurname(userinfoplus.getFamilyName())
                    .build();
            usersWebService.createUser(user);
        }
        logger.info("Authentication success of user: " + email);
        return usersWebService.findAuthUserDTOByEmail(email);
    }

    private void setSessionAttributes(HttpServletRequest req, AuthUserDTO verifiedUser) {
        req.getSession().setAttribute(USER_ID_ATTR, verifiedUser.getId());
        req.getSession().setAttribute(USER_TYPE_ATTR, verifiedUser.getPermissionLevel().toString());
    }

    private void setSessionAtrrUserType(HttpServletRequest req) {
        if (req.getSession().getAttribute(USER_TYPE_ATTR) == null) {
            req.getSession().setAttribute(USER_TYPE_ATTR, USER_TYPE_GUEST);
        }
    }
}