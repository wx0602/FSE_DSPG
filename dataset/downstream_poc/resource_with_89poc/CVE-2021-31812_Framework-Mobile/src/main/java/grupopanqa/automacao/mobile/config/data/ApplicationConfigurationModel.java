package grupopanqa.automacao.mobile.config.data;

import org.openqa.selenium.remote.DesiredCapabilities;

import java.util.Map;

public class ApplicationConfigurationModel {
    private String id;
    private MobilePlatform platform;
    private Map<String,?> capabilities;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public MobilePlatform getPlatform() {
        return platform;
    }

    public void setPlatform(MobilePlatform platform) {
        this.platform = platform;
    }

    public Map<String, ?> getCapabilities() {
        return capabilities;
    }

    public void setCapabilities(Map<String, ?> capabilities) {
        this.capabilities = capabilities;
    }

    public DesiredCapabilities getApplicationCapabilities(){
        return new DesiredCapabilities(this.capabilities);
    }
}
