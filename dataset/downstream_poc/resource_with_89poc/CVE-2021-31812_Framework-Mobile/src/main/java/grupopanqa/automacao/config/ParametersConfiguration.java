package grupopanqa.automacao.config;

import static grupopanqa.automacao.dados.ConfiguracaoDados.recuperarValor;

/**
 * Classe com os parametros que serão recebidos por linha de comando,
 * podendo ter valores padrão determinados
 */
public enum ParametersConfiguration {
    DEVICE_JSON("deviceJson", "src/test/resources/device.json"),
    DEVICE_IOS_JSON("deviceJson", "src/test/resources/device_ios.json"),
    APPIUM_SERVER_ADDRESS("APPIUM_SERVER", "http://poc-device-farm.bancopan.com.br:9090/wd/hub"),
    RUNTIME_ENVIRONMENT("runtimeEnv", "LOCAL"),
    RUNTIME_TYPE("runtimeType", "NEW"),
    DEVICE_ID("deviceId", "");

    private final String defaultValue;
    private final String key;

    public String value() {
    	return recuperarValor(this.key, this.defaultValue);
    }

    ParametersConfiguration(String key, String defaultValue) {
        this.defaultValue = defaultValue;
        this.key = key;
    }
}
