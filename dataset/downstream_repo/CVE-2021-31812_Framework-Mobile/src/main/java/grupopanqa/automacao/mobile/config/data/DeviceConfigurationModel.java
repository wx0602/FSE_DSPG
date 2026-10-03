package grupopanqa.automacao.mobile.config.data;

import org.openqa.selenium.remote.DesiredCapabilities;

import java.util.Map;

public class DeviceConfigurationModel {
    private String id;
    private DeviceType type;
    private Map<String, ?> capabilities;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public DeviceType getType() {
        return type;
    }

    public void setType(DeviceType type) {
        this.type = type;
    }

    public Map<String, ?> getCapabilities() {
        return capabilities;
    }

    public void setCapabilities(Map<String, ?> capabilities) {
        this.capabilities = capabilities;
    }

    public DesiredCapabilities getDeviceCapabilities(){
        return new DesiredCapabilities(this.capabilities);
    }
}
