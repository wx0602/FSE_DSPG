package grupopanqa.automacao.mobile.config.data;

import grupopanqa.automacao.util.EnumFramework;
import org.openqa.selenium.remote.DesiredCapabilities;

import java.util.HashMap;
import java.util.List;

public class MobileConfiguration {
    private EnumFramework.Ambiente ambiente;
    private ReportConfigurationModel report;
    private ApplicationConfigurationModel app;
    private SideServiceConfigurationModel sideService;
    private HashMap<String,?> capabilities;
    private List<DeviceConfigurationModel> devices;

    public EnumFramework.Ambiente getAmbiente() {
        return ambiente;
    }

    public void setAmbiente(EnumFramework.Ambiente ambiente) {
        this.ambiente = ambiente;
    }

    public ReportConfigurationModel getReport() {
        return report;
    }

    public void setReport(ReportConfigurationModel report) {
        this.report = report;
    }

    public ApplicationConfigurationModel getApp() {
        return app;
    }

    public void setApp(ApplicationConfigurationModel app) {
        this.app = app;
    }

    public HashMap<String, ?> getCapabilities() {
        return capabilities;
    }

    public void setCapabilities(HashMap<String, String> capabilities) {
        this.capabilities = capabilities;
    }

    public DesiredCapabilities getGeneralCapabilities() {
        return new DesiredCapabilities(this.capabilities);
    }

    public List<DeviceConfigurationModel> getDevices() {
        return devices;
    }

    public void setDevices(List<DeviceConfigurationModel> devices) {
        this.devices = devices;
    }

    public SideServiceConfigurationModel getSideService() {
        return sideService;
    }

    public void setSideService(SideServiceConfigurationModel sideService) {
        this.sideService = sideService;
    }
}
