package grupopanqa.automacao.mobile.services.impl;

import com.browserstack.local.Local;
import grupopanqa.automacao.config.ParametersConfiguration;
import grupopanqa.automacao.mobile.config.data.SideServiceConfigurationModel;
import grupopanqa.automacao.mobile.services.ExecutionSideService;
import grupopanqa.automacao.util.CaCertificado;
import grupopanqa.automacao.util.LogUtil;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.remote.DesiredCapabilities;

import java.util.HashMap;
import java.util.UUID;

public class BrowserStackSideService implements ExecutionSideService {
    private final SideServiceConfigurationModel config;

    public BrowserStackSideService(SideServiceConfigurationModel config){
        this.config = config;
    }

    @Override
    public void beforeDriver() {

    }

    @Override
    public DesiredCapabilities generateCapabilities() {
        DesiredCapabilities caps = new DesiredCapabilities(config.getCapabilities());
        caps.setCapability("browserstack.local", System.getenv("BROWSERSTACK_LOCAL"));
        caps.setCapability("browserstack.localIdentifier", System.getenv("BROWSERSTACK_LOCAL_IDENTIFIER"));
        LogUtil.info(String.format("[SIDE-SERVICE][CAPABILITIES] Gerando capabilities: %s",caps.toString()));
        return caps;
    }

    @Override
    public void afterDriver(WebDriver driver) {

    }
    @Override
    public void stop(){

    }
}
