package com.korpodrony.oauth;

import com.google.api.client.googleapis.auth.oauth2.GoogleAuthorizationCodeFlow;
import com.google.api.client.http.GenericUrl;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.jackson2.JacksonFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.List;
import java.util.Objects;
import java.util.Properties;

public class GoogleLoginCommons {

  private static final Logger logger = LoggerFactory.getLogger("com.korpodrony.oauth");
  private static final String OAUTH_FILE_NAME = "oauth.properties";
  private static final List<String> SCOPES = null;

  static String buildRedirectUri(HttpServletRequest req) {
    GenericUrl url = new GenericUrl(req.getRequestURL().toString());
    url.setRawPath(getProperty("redirect.url"));
    return url.build();
  }

  static GoogleAuthorizationCodeFlow buildFlow() {
    return new GoogleAuthorizationCodeFlow.Builder(
        new NetHttpTransport(),
        JacksonFactory.getDefaultInstance(), getProperty("client.id"),
        getProperty("secret"), SCOPES)
        .setAccessType("online")
        .build();
  }

  private static String getProperty(String property) {
    Properties properties = new Properties();
    try {
      properties.load(Objects.requireNonNull(Thread.currentThread()
          .getContextClassLoader().getResource(OAUTH_FILE_NAME))
          .openStream());
    } catch (IOException e) {
      logger.error(e.getMessage());
    }
    return properties.getProperty(property);
  }
}
