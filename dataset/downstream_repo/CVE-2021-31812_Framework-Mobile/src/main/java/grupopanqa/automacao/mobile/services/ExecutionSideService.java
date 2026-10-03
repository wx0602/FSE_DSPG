package grupopanqa.automacao.mobile.services;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.remote.DesiredCapabilities;

public interface ExecutionSideService {

    void beforeDriver();
    DesiredCapabilities generateCapabilities();
    void afterDriver(WebDriver driver);

    void stop();
}