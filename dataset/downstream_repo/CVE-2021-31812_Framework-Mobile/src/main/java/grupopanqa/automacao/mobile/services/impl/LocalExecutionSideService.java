package grupopanqa.automacao.mobile.services.impl;

import grupopanqa.automacao.mobile.services.ExecutionSideService;
import grupopanqa.automacao.util.LogUtil;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.remote.DesiredCapabilities;

public class LocalExecutionSideService implements ExecutionSideService {
    @Override
    public void beforeDriver() {
        System.out.println("Nada a fazer aqui");
    }

    @Override
    public DesiredCapabilities generateCapabilities() {
        System.out.println("Nada a fazer aqui");
        return null;
    }

    @Override
    public void afterDriver(WebDriver driver) {
        System.out.println("Nada a fazer aqui");
    }

    @Override
    public void stop() {
        LogUtil.info("Nada a fazer aqui");
    }
}
