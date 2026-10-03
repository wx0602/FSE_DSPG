package grupopanqa.automacao.mobile.services.impl;

import grupopanqa.automacao.mobile.config.data.SideServiceConfigurationModel;
import grupopanqa.automacao.mobile.services.ExecutionSideService;
import grupopanqa.automacao.util.LogUtil;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.remote.DesiredCapabilities;

public class SaucelabsSideService implements ExecutionSideService {
    private final SideServiceConfigurationModel config;


    public SaucelabsSideService(SideServiceConfigurationModel config) {
        this.config = config;
    }

    @Override
    public void beforeDriver() {
        LogUtil.info("[SIDE-SERVICE][BEFORE-DRIVER] Nada a fazer aqui");
    }

    @Override
    public DesiredCapabilities generateCapabilities() {
        DesiredCapabilities capabilities = new DesiredCapabilities(this.config.getCapabilities());
        capabilities.setCapability("tunnelIdentifier", System.getenv("TUNNEL_IDENTIFIER"));
        LogUtil.info(String.format("[SIDE-SERVICE][CAPABILITIES] Gerando capabilities: %s",capabilities.toString()));
        return capabilities;
    }

    @Override
    public void afterDriver(WebDriver driver) {
        LogUtil.info("[SIDE-SERVICE][AFTER-DRIVER] Nada a fazer aqui");

    }

    @Override
    public void stop() {
        LogUtil.info("[SIDE-SERVICE][STOP] Nada a fazer aqui");
    }
}
