package grupopanqa.automacao.apiRest;

import grupopanqa.automacao.util.EnumFramework.ApiTipoBody;

import java.util.Properties;

/**
 * Classe com metodos responsaveis pela construcao da API
 * @author 800041563
 *
 */
public class ConstrutorApi {
	
	//ExecutorApi executorApi = new ExecutorApi();
	//ConfiguracaoDados configFile;
	//String endPointCaminho;
	//String sufixoEndPointCaminho;
	//ConfiguracaoDados endPointFile;
	//ConfiguracaoDados endPointPathFile;
	//public String endPoint = "";
	//public String endPointPath = "";
	//public Properties header = null;
	//public String body = "";
	//public Arquivo arquivo = new Arquivo();	
	public Api api = new Api();
	

	/**
	 * Recebe a estrutura da API por parametro e monta a api
	 * @param endPoint
	 * @param endPointPath
	 * @param header
	 * @param body
	 * @return API
	 */
	public Api montarApi(String endPoint,String endPointPath,Properties header,String body){
		api.setEndpoint(endPoint);
		api.setEndpointPath(endPointPath);
		api.setHeader(header);
		Body entidadeBody = new Body();
		entidadeBody.setTipoBody(ApiTipoBody.Json);
		entidadeBody.setBodyJson(body);
		api.setBody(entidadeBody);
		return api;
	}
	
	public Api montarApi(String endPoint,String endPointPath,Properties header,Properties body){
		api.setEndpoint(endPoint);
		api.setEndpointPath(endPointPath);
		api.setHeader(header);
		Body entidadeBody = new Body();
		entidadeBody.setTipoBody(ApiTipoBody.Properties);
		entidadeBody.setBodyProperties(body);
		api.setBody(entidadeBody);
		return api;
	}
}
