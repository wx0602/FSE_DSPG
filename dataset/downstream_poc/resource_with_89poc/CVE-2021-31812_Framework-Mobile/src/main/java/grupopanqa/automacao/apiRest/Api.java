package grupopanqa.automacao.apiRest;

import java.util.Properties;

/**
 * Classe entidade para auxilio na criação e manipulação de APIs
 * @author 800041563
 *
 */
public class Api {

	private String endpoint;
	private String endpointPath;
	private Properties header;
	private Body body;

	public String getEndpoint() {
		return endpoint;
	}
	public void setEndpoint(String endpoint) {
		this.endpoint = endpoint;
	}
	public String getEndpointPath() {
		return endpointPath;
	}
	public void setEndpointPath(String sufixoEndpoint) {
		this.endpointPath = sufixoEndpoint;
	}
	public Properties getHeader() {
		return header;
	}
	public void setHeader(Properties header) {
		this.header = header;
	}
	public Body getBody() {
		return body;
	}
	public void setBody(Body body) {
		this.body = body;
	}
}
