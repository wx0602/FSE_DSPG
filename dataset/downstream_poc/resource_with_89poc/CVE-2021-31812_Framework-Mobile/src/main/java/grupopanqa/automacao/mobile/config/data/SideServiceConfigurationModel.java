package grupopanqa.automacao.mobile.config.data;

import java.util.Map;

public class SideServiceConfigurationModel {
    private String key;
    private Map<String,?> extras;
    private Map<String,?> capabilities;

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public Map<String, ?> getExtras() {
        return extras;
    }

    public void setExtras(Map<String, ?> extras) {
        this.extras = extras;
    }

    public Map<String, ?> getCapabilities() {
        return capabilities;
    }

    public void setCapabilities(Map<String, ?> capabilities) {
        this.capabilities = capabilities;
    }
}
