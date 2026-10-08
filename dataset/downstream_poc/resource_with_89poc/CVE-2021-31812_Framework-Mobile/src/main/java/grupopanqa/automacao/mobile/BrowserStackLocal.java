package grupopanqa.automacao.mobile;

import com.browserstack.local.Local;
import grupopanqa.automacao.util.EnumFramework.Status;
import org.apache.http.NameValuePair;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.message.BasicNameValuePair;
import org.openqa.selenium.remote.SessionId;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

/**
 * Classe responsável realizar a conexao com o BrowserStack e permitir a conexão
 * local (acesso dos celulares da browserstack na rede interna)
 * 
 * @author 800041563
 *
 */
public class BrowserStackLocal {

	Local bsLocal;
	Map<String, String> options = new HashMap<String, String>();
	static String usuarioLogin = "";
	static String accessKey = "";

	public BrowserStackLocal(String usuarioLogin, String accessKey) {
		BrowserStackLocal.usuarioLogin = usuarioLogin;
		BrowserStackLocal.accessKey = accessKey;
	}

	/**
	 * Abre conexao local com o browserstack. Para testes em paralelo, é necessário
	 * informar o id da thread para que seja instanciado uma conexão por execução de
	 * teste
	 * 
	 * @param idLocalIdentifier
	 */
	public void conectaBrowserstackLocal(String idLocalIdentifier) {
		options.put("localIdentifier", String.valueOf(Thread.currentThread().getId()));
		conectaBrowserstackLocal();
	}

	/**
	 * Abre conexao local com o browserstack.
	 */
	public void conectaBrowserstackLocal() {
		bsLocal = new Local();
		options.put("key", accessKey);
		try {
			bsLocal.start(options);
		} catch (Exception erro) {
			TestBaseMobile.logReport(Status.FAIL, "Falha ao realizar conexão local com o BrowserStack. Erro: " + erro);
		}
	}

	/**
	 * Finaliza a instância da conexao local
	 */
	public void finalizaBrowserstackLocal() {
		try {
			bsLocal.stop(options);
		} catch (Exception erro) {
			TestBaseMobile.logReport(Status.INFO, "Falha ao finalizar conexão local com o BrowserStack. Erro: " + erro);
		}
	}

	/**
	 * Envia o status da execução e descrição para a sessão da browserstack (paraque seja possível visualizar as informações 
	 * na própria tela da browserstack
	 * @param sessionId Sessão da execução
	 * @param statusPassed Boolean true - passou / false - falhou
	 * @param detalhesExecucao Descrição da execução
	 * @throws URISyntaxException
	 * @throws UnsupportedEncodingException
	 * @throws IOException
	 */
	public static void setStatusSessao(SessionId sessionId, Boolean statusPassed, String detalhesExecucao)
			throws URISyntaxException, UnsupportedEncodingException, IOException {
		URI uri = new URI("https://" + usuarioLogin + ":" + accessKey + "@api.browserstack.com/app-automate/sessions/"
				+ sessionId.toString() + ".json");
		HttpPut putRequest = new HttpPut(uri);
		String status = "";
		if (statusPassed) {
			status = "completed";
		} else {
			status = "error";
		}
		ArrayList<NameValuePair> nameValuePairs = new ArrayList<NameValuePair>();
		nameValuePairs.add((new BasicNameValuePair("status", status)));
		nameValuePairs.add((new BasicNameValuePair("reason", detalhesExecucao)));
		putRequest.setEntity(new UrlEncodedFormEntity(nameValuePairs));
		HttpClientBuilder.create().build().execute(putRequest);
	}
}
