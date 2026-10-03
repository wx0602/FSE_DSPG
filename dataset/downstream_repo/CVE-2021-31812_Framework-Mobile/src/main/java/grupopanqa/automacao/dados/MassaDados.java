package grupopanqa.automacao.dados;

import grupopanqa.automacao.util.Arquivo;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.Tempo;
import grupopanqa.automacao.util.TestBase;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.*;

/**
 * Classe responsavel por organizar e controlar as massas de dados utilizados
 * durante a execucao do teste
 * 
 * @author 800041563
 *
 */
public class MassaDados {
	// Massas disponíveis para uso (<id_categoria_massa, array_objeto_json>)
	private static Map<String, JSONArray> mapMassasDisponiveis = new HashMap<String, JSONArray>();
	// Massa estática utilizada por todos os testes (<id_massa, valor_massa>)
	private static Map<String, String> massa = new HashMap<String, String>();
	// Massas que estão sendo utilizadas por algum teste/thread (<id_thread,
	// <id_categoria_massa, objeto_json>>)
	private static Map<String, Map<String, JSONObject>> mapMassasReservadas = new HashMap<String, Map<String, JSONObject>>();

	/**
	 * Realiza a consulta da chave e retorna o valor respectivo
	 * 
	 * @param chave String com o valor da chave
	 * @return String com o valor referente a chave. Caso nao seja encontrado a
	 *         chave, e retornado null
	 */
	public static String ConsultarValor(String chave) {

		String valor;

		if (verificaExistePropriedade(chave)) {
			valor = massa.get(chave);
		} else {
			valor = null;
		}

		return valor;

	}

	public static String ConsultarValor(String thread_id, String chave) {
		return ConsultarValor("thread_" + thread_id + "_id_" + chave);

	}

	/**
	 * Armazena chave/valor informado por parametro
	 * 
	 * @param chave
	 * @param valor
	 */
	synchronized public static void armazenarDados(String chave, String valor) {
		massa.put(chave, valor);
	}

	/**
	 * Armazena chave/valor informado por parametro
	 * 
	 * @param chave
	 * @param valor
	 */
	synchronized public static void armazenarDados(String thread_id, String chave, String valor) {
		String chaveComThread = chave = "thread_" + thread_id + "_id_" + chave;
		armazenarDados(chaveComThread, valor);
	}

	/**
	 * Remove chave informado por parametro
	 * 
	 * @param chave
	 */
	synchronized public static void removerDados(String chave) {
		massa.remove(chave);
	}

	synchronized public static void removerDados(String thread_id, String chave) {
		massa.remove("thread_" + thread_id + "_id_" + chave);
	}

	/**
	 * Remove todas as chaves e valores
	 */
	synchronized public static void removerTodosDados() {
		massa.clear();
	}

	/**
	 * Remove todas as chaves e valores criados por uma determinada thread (para
	 * testes em paralelo)
	 * 
	 * @param thread_id - ID da thread que esta sendo executada
	 */
	synchronized public static void removerTodosDados(String thread_id) {

		liberarMassa(thread_id);
		String parte_chave = "thread_" + thread_id + "_id_";
		massa.entrySet().removeIf(e -> e.getKey().contains(parte_chave));

	}

	/**
	 * Verifica a existencia da chave
	 * 
	 * @param chave
	 * @return Boolean True - Existe / False - Nao existe
	 */
	public static Boolean verificaExistePropriedade(String chave) {

		Boolean existePropriedade = massa.containsKey(chave);
		return existePropriedade;

	}

	/**
	 * Recebe dados e retorna com o valor atualizado de acordo com a massa de dados
	 * existente
	 * 
	 * @param valor             String a ser atualizada
	 * @param delimitadorInicio String contendo valor a ser utilizado como
	 *                          delimitador inicial
	 * @param delimitadorFim    String contendo valor a ser utilizado como
	 *                          delimitador final
	 * @return String atualizado
	 */
	public static String atualizarValorMassaDados(String valor, String delimitadorInicio, String delimitadorFim) {
		while (valor.contains(delimitadorInicio)) {
			int pos1 = valor.indexOf(delimitadorInicio);
			int pos2 = valor.indexOf(delimitadorFim);
			String paramComChave = valor.substring(pos1, pos2 + delimitadorFim.length());
			String param = paramComChave.replace(delimitadorInicio, "").replace(delimitadorFim, "");
			String paramValor = ConsultarValor(param);
			if (paramValor == null) {
				paramValor = "";
			}
			valor = valor.replace(paramComChave, paramValor);
		}
		return valor;
	}

	/**
	 * Recebe o properties e atualiza os valores de acordo com dados da massa de
	 * dados
	 * 
	 * @param properties         Dados a serem atualizados
	 * @param delimitadorInicial String com o delimitador que informa o inicio do
	 *                           parametro
	 * @param delimitadorFinal   String com o delimitador que informa o fim do
	 *                           parametro
	 * @return Properties contendo os dados atualizados
	 * @throws IOException
	 */
	public static Properties atualizarValorMassaDadosProperties(Properties properties, String delimitadorInicial,
			String delimitadorFinal) throws IOException {
		// Properties propertieHeader =
		// arquivo.retornarProperties(enumHeader.getDescricao());
		Enumeration<?> propertyNames = properties.propertyNames();
		while (propertyNames.hasMoreElements()) {
			String propriedade = (String) propertyNames.nextElement();
			String valor = properties.getProperty(propriedade);
			valor = MassaDados.atualizarValorMassaDados(valor, delimitadorInicial, delimitadorFinal);
			properties.setProperty(propriedade, valor);
		}
		return properties;
	}

	public static JSONObject converterArquivoMassaEmObjetoJson(String caminhoMassa, String nomeObjetoJson) {
		JSONObject jsonObjeto = null;
		String jsonMassaCaminho = "";
		try {
			jsonMassaCaminho = ConfiguracaoDados.atualizarValorMassa(caminhoMassa, "{{", "}}");
			String jsonTexto = Arquivo.retornarTexto(jsonMassaCaminho);
			jsonObjeto = new JSONObject(jsonTexto).getJSONObject(nomeObjetoJson);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Erro ao buscar o arquivo: '" + jsonMassaCaminho + "'");
		} catch (JSONException e) {
			TestBase.logReport(Status.FAIL, "Nao foi possivel recuperar o objeto: '" + nomeObjetoJson
					+ "' no arquivo: '" + jsonMassaCaminho + "'");
		}
		return jsonObjeto;

	}

	public static JSONArray converterArquivoMassaEmArrayJson(String caminhoMassa, String nomeObjetoJson) {
		JSONArray jsonArray = null;
		String jsonMassaCaminho = "";
		try {
			jsonMassaCaminho = ConfiguracaoDados.atualizarValorMassa(caminhoMassa, "{{", "}}");
			String jsonTexto = Arquivo.retornarTexto(jsonMassaCaminho);
			jsonArray = new JSONObject(jsonTexto).getJSONArray(nomeObjetoJson);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Erro ao buscar o arquivo: '" + jsonMassaCaminho + "'");
		} catch (JSONException e) {
			TestBase.logReport(Status.FAIL, "Nao foi possivel recuperar o array do objeto: '" + nomeObjetoJson
					+ "' no arquivo: '" + jsonMassaCaminho + "'");
		}
		return jsonArray;

	}

	public static Object converterArquivoMassaEmJson(String caminhoMassa, String nomeObjetoJson) {
		Object json = null;
		String jsonMassaCaminho = "";
		try {
			jsonMassaCaminho = ConfiguracaoDados.atualizarValorMassa(caminhoMassa, "{{", "}}");
			String jsonTexto = Arquivo.retornarTexto(jsonMassaCaminho);

			if (new JSONObject(jsonTexto).get(nomeObjetoJson) instanceof JSONObject) {
				json = new JSONObject(jsonTexto).getJSONObject(nomeObjetoJson);
			} else if (new JSONObject(jsonTexto).get(nomeObjetoJson) instanceof JSONArray) {
				json = new JSONObject(jsonTexto).getJSONArray(nomeObjetoJson);
			}

		} catch (IOException e) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Erro ao buscar o arquivo: '" + jsonMassaCaminho + "'");
		} catch (JSONException e) {
			TestBase.logReport(Status.FAIL,
					"Nao foi possivel recuperar: '" + nomeObjetoJson + "' no arquivo: '" + jsonMassaCaminho + "'");
		}
		return json;

	}

	public static void adicionarVariaveisMassaDados(JSONObject jsonObjeto) {
		adicionarVariaveisMassaDados("", jsonObjeto);
	}

	synchronized public static void adicionarVariaveisMassaDados(String thread_id, JSONObject jsonObjeto) {
		Iterator<String> chaves = jsonObjeto.keys();
		while (chaves.hasNext()) {
			String chave = chaves.next();
			String valor = jsonObjeto.get(chave).toString();
			if (!thread_id.equals("")) {
				chave = "thread_" + thread_id + "_id_" + chave;
			}
			armazenarDados(chave, valor);
		}
	}

	/**
	 * Carrega a massa de um Json e converte em dados no hashmap (chave/valor)
	 * 
	 * @param objetoJson ObjetoJson a ser filtrado do arquivo Json
	 */
	public static void carregarMassaDados(String caminhoMassa, String nomeObjetoJson) {
		JSONObject massaObjetoJson = converterArquivoMassaEmObjetoJson(caminhoMassa, nomeObjetoJson);
		adicionarVariaveisMassaDados(massaObjetoJson);
	}

	/**
	 * Carrega a massa de um Json e converte em dados no hashmap (chave/valor),
	 * diferenciando pelo id da thread em caso de teste com paralelismo
	 * 
	 * @param objetoJson ObjetoJson a ser filtrado do arquivo Json
	 */
	public static void carregarMassaDados(String thread_id, String caminhoMassa, String nomeObjetoJson) {
		Object massaJson = converterArquivoMassaEmJson(caminhoMassa, nomeObjetoJson);
		if (massaJson instanceof JSONObject) {
			adicionarVariaveisMassaDados(thread_id, (JSONObject) massaJson);
		} else if (massaJson instanceof JSONArray) {
			if (!mapMassasDisponiveis.containsKey(nomeObjetoJson)) {
				mapMassasDisponiveis.put(nomeObjetoJson, (JSONArray) massaJson);
			}
			JSONObject massaObjetoJson = reservarMassa(nomeObjetoJson, thread_id);
			adicionarVariaveisMassaDados(thread_id, massaObjetoJson);
		}
	}

	private static JSONObject reservarMassa(String nomeObjetoJson, String thread_id) {
		JSONObject massaObjetoJson = retirarMassaListaDisponiveis(nomeObjetoJson);
		adicionarMassaListaReservadas(massaObjetoJson, nomeObjetoJson, thread_id);
		return massaObjetoJson;
	}

	private static void adicionarMassaListaReservadas(JSONObject massaObjetoJson, String nomeObjetoJson,
			String thread_id) {
		Map<String, JSONObject> mapMassaReservada = new HashMap<String, JSONObject>();
		mapMassaReservada.put(nomeObjetoJson, massaObjetoJson);
		mapMassasReservadas.put(thread_id, mapMassaReservada);
	}

	private static JSONObject retirarMassaListaDisponiveis(String nomeObjetoJson) {
		int cont = 0;

			while (mapMassasDisponiveis.get(nomeObjetoJson).length() == 0) {
				if (cont > 300) {
					TestBase.logReport(Status.FAIL,
							"Após espera de 300 segundos não foi disponibilizada a massa solicitada: "
									+ nomeObjetoJson);
				}
				Tempo.aguardarSegundos(1);

			}
			cont++;
		JSONObject massaObjetoJson = (JSONObject) mapMassasDisponiveis.get(nomeObjetoJson).remove(0);
		// mapMassasDisponiveis.get(nomeObjetoJson).remove(0);
		return massaObjetoJson;
	}

	synchronized public static void liberarMassa(String thread_id) {
		Map<String, JSONObject> mapMassa = mapMassasReservadas.remove(thread_id);
		if (mapMassa != null) {
			for (Map.Entry<String, JSONObject> massa : mapMassa.entrySet()) {
				mapMassasDisponiveis.get(massa.getKey()).put(massa.getValue());
			}
		}
	}
}
