package grupopanqa.automacao.mobile.services;

import grupopanqa.automacao.config.RuntimeEnvironmentType;
import grupopanqa.automacao.mobile.config.data.SideServiceConfigurationModel;
import grupopanqa.automacao.mobile.services.impl.BrowserStackSideService;
import grupopanqa.automacao.mobile.services.impl.LocalExecutionSideService;
import grupopanqa.automacao.mobile.services.impl.SaucelabsSideService;

public class ExecutionSideServiceFactory {
    public static ExecutionSideService createInstance(RuntimeEnvironmentType runtimeEnvironment, SideServiceConfigurationModel config){
        ExecutionSideService sideService;
        switch (runtimeEnvironment){
            case SAUCELABS:
                sideService = new SaucelabsSideService(config);
                break;
            case BROWSERSTACK:
                sideService = new BrowserStackSideService(config);
                break;
            case LOCAL:
            default:
                sideService = new LocalExecutionSideService();
            break;
        }
        return sideService;
    }
}
