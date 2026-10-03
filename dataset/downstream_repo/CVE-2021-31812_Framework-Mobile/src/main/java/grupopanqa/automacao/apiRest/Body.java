package grupopanqa.automacao.apiRest;

import grupopanqa.automacao.util.EnumFramework.ApiTipoBody;

import java.util.Properties;
/**
 * Classe entidade que armazena o body (podendo ser por properties ou json)
 * @author 800041563
 *
 */
public class Body {

	private ApiTipoBody tipoBody;
	private String bodyJson;
	private Properties bodyProperties;
	
	public ApiTipoBody getTipoBody() {
		return tipoBody;
	}
	public void setTipoBody(ApiTipoBody tipoBody) {
		this.tipoBody = tipoBody;
	}
	public String getBodyJson() {
		return bodyJson;
	}
	public void setBodyJson(String bodyJson) {
		this.bodyJson = bodyJson;
	}
	public Properties getBodyProperties() {
		return bodyProperties;
	}
	public void setBodyProperties(Properties bodyProperties) {
		this.bodyProperties = bodyProperties;
	}
}
