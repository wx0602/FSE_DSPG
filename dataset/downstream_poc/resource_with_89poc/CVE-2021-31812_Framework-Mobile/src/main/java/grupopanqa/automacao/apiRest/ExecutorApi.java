package grupopanqa.automacao.apiRest;

import com.jayway.restassured.RestAssured;
import com.jayway.restassured.config.EncoderConfig;
import com.jayway.restassured.http.ContentType;
import com.jayway.restassured.response.Response;
import com.jayway.restassured.specification.RequestSpecification;
import grupopanqa.automacao.util.EnumFramework.ApiTipoBody;

import java.io.IOException;
import java.util.Enumeration;
import java.util.Properties;

/**
 * Classe com metodos para execucao da API
 * 
 * @author 800041563
 *
 */
public class ExecutorApi {

	/**
	 * Realiza o envio (POST) da api
	 * 
	 * @param api API a ser enviada
	 * @return Retorna o response gerado pelo envio da API
	 * @throws IOException
	 */
	public Response apiPost(Api api) throws IOException {

		// Monta o endPoint
		RestAssured.baseURI = api.getEndpoint();

		// Montar o path do endPoint Base
		String pathEndpoint = api.getEndpointPath();

		// Monta o header
		RequestSpecification request = RestAssured.given();
		request = montarHeader(request, api.getHeader());

		// Monta o body
		request = montarBody(request, api);

		// Envia API e gera response
		Response response = request.post(pathEndpoint);
		return response;

	}

	/**
	 * Realiza o envio (GET) da api
	 * 
	 * @param api API a ser enviada
	 * @return Retorna o response gerado pelo envio da API
	 * @throws IOException
	 */
	public Response apiGet(Api api) throws IOException {

		// Monta o endPoint
		RestAssured.baseURI = api.getEndpoint();

		// Montar o path do endPoint Base
		String pathEndpoint = api.getEndpointPath();

		// Monta o header
		RequestSpecification request = RestAssured.given();
		request = montarHeader(request, api.getHeader());

		// Get não possui Body

		// Envia API e gera response
		Response response = request.get(pathEndpoint);
		return response;

	}

	/**
	 * Realiza o envio (DELETE) da api
	 * 
	 * @param api API a ser enviada
	 * @return Retorna o response gerado pelo envio da API
	 * @throws IOException
	 */
	public Response apiDelete(Api api) throws IOException {

		// Monta o endPoint
		RestAssured.baseURI = api.getEndpoint();

		// Montar o path do endPoint Base
		String pathEndpoint = api.getEndpointPath();

		// Monta o header
		RequestSpecification request = RestAssured.given();
		request = montarHeader(request, api.getHeader());

		// Delete não possui Body

		// Envia API e gera response
		Response response = request.delete(pathEndpoint);
		return response;

	}

	/**
	 * Realiza o envio (PUT) da api
	 * 
	 * @param api API a ser enviada
	 * @return Retorna o response gerado pelo envio da API
	 * @throws IOException
	 */
	public Response apiPut(Api api) throws IOException {

		// Monta o endPoint
		RestAssured.baseURI = api.getEndpoint();

		// Montar o path do endPoint Base
		String pathEndpoint = api.getEndpointPath();

		// Monta o header
		RequestSpecification request = RestAssured.given();
		request = montarHeader(request, api.getHeader());

		// Monta o Body
		request = montarBody(request, api);

		// Envia API e gera response
		Response response = request.put(pathEndpoint);
		return response;

	}

	/**
	 * Monta o Header
	 * 
	 * @param request Request que será incluido o Header
	 * @param propertieHeader Arquivo property onde está armazenado o Header
	 * @return Request com o Header
	 * @throws IOException
	 */
	public RequestSpecification montarHeader(RequestSpecification request, Properties propertieHeader)
			throws IOException {
		Enumeration<?> propertyNames = propertieHeader.propertyNames();
		while (propertyNames.hasMoreElements()) {
			String propriedade = (String) propertyNames.nextElement();
			String valor = propertieHeader.getProperty(propriedade);
			request.header(propriedade, valor);
		}
		return request;
	}

	/**
	 * Monta o Body
	 * 
	 * @param request  Request que sera adicionado o Body
	 * @param api Api contendo o body que sera adicionado no Request
	 * @return Request com o body
	 */
	public RequestSpecification montarBody(RequestSpecification request, Api api) {
		Body body = api.getBody();

		// O body pode ser do tipo Properties ou Json. Para cada tipo, a montagem e
		// diferente
		// Tipo Properties
		if (body.getTipoBody() == ApiTipoBody.Properties) {
			request.config(RestAssured.config().encoderConfig(
					EncoderConfig.encoderConfig().encodeContentTypeAs("x-www-form-urlencoded", ContentType.JSON)))
					.contentType("x-www-form-urlencoded; charset = UTF-8");
			Enumeration<?> propertyNames = body.getBodyProperties().propertyNames();
			while (propertyNames.hasMoreElements()) {
				String propriedade = (String) propertyNames.nextElement();
				String valor = body.getBodyProperties().getProperty(propriedade);
				request.formParam(propriedade, valor);
			}
		}
		// Tipo Json
		else if (body.getTipoBody() == ApiTipoBody.Json) {
			request.body(body.getBodyJson());
		}

		return request;
	}

}
