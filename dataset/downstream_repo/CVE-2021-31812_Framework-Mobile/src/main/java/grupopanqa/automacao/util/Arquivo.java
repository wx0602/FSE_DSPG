package grupopanqa.automacao.util;

import com.google.gson.GsonBuilder;
import grupopanqa.automacao.mobile.config.data.MobileConfiguration;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;


/**
 * Classe com metodos que auxiliam na automação de arquivos gerais (txt, json, properties...)
 * @author 800041563
 *
 */
public class Arquivo {
	
	/**
	 * Recebe o caminho de um arquivo e retorna o tipo Properties
	 * @param caminhoArquivo Caminho do arquivo
	 * @return Properties 
	 */
	public static Properties retornarProperties(String caminhoArquivo) {
		Properties properties = new Properties();
		try {
			BufferedReader reader;
			reader = new BufferedReader(new FileReader(caminhoArquivo));
			properties.load(reader);
			reader.close();
		} catch (IOException e) {
			TestBase.logReport(EnumFramework.Status.FAIL, "Erro ao recuperar o properties em: " + caminhoArquivo + ". Erro: " + e);
		}
		return properties;
	}

	/**
	 * Recebe o caminho de um arquivo (txt, json...), realiza a leitura e retorna o seu texto
	 * @param caminhoArquivo Caminho do arquivo
	 * @return String Texto que está no arquivo
	 */
	public static String retornarTexto(String caminhoArquivo) {
		String arquivo = "";
		String texto = "";
		BufferedReader reader;
		try {

			reader = new BufferedReader(new FileReader(caminhoArquivo));
			arquivo = reader.readLine();
			do{
				texto = texto + arquivo;
				arquivo = reader.readLine();
			}while(arquivo != null);

			reader.close();
		} catch (IOException e) {
			TestBase.logReport(EnumFramework.Status.FAIL, "Erro ao recuperar o texto do arquivo: " + caminhoArquivo + ". Erro: " + e);
		}
		return texto;
		
	}
	
	/**
	 * Recebe o caminho de um arquivo (txt, json...), realiza a leitura e retorna uma lista com todas as linhas encontradas
	 * @param caminhoArquivo Caminho do arquivo
	 * @return String Texto que está no arquivo
	 */
	public static List<String> retornarList(String caminhoArquivo) {
		List<String> listaLinhas = new ArrayList<String>();
		String arquivo = "";
		BufferedReader reader;
		try {

			reader = new BufferedReader(new FileReader(caminhoArquivo));
			arquivo = reader.readLine();
			do{
				listaLinhas.add(arquivo);
				arquivo = reader.readLine();
			}while(arquivo != null);

			reader.close();
		} catch (IOException e) {
			TestBase.logReport(EnumFramework.Status.FAIL, "Erro ao recuperar a lista de linhas do arquivo: " + caminhoArquivo + ". Erro: " + e);
		}
		return listaLinhas;
		
	}
	
	/**
	 * Adiciona uma nova linha com texto no arquivo desejado
	 * @param caminhoArquivo Caminho do arquivo
	 * @param texto Texto a ser inserido no arquivo
	 */
	public static void adicionarTexto(String caminhoArquivo, String texto){
		try {
			BufferedWriter buffWrite;
			FileWriter fileWriter = new FileWriter(caminhoArquivo, true);
			buffWrite = new BufferedWriter(fileWriter);
			buffWrite.newLine();
	        buffWrite.append(texto);
	        buffWrite.close();
		} catch (IOException e) {
			TestBase.logReport(EnumFramework.Status.FAIL, "Erro ao adicionar o texto " + texto + " no arquivo: " + caminhoArquivo + ". Erro: " + e);
		}

	}
	
	
	/**
	 * Recebe o caminho do arquivo Json, converte e retorna o objeto JsonObject
	 * @param caminhoArquivo Caminho do arquivo
	 * @return JSONObject
	 */
	public static JSONObject retornarJsonObject(String caminhoArquivo) {
		JSONParser parser = new JSONParser();
		JSONObject jsonObject = null;
		try {
			jsonObject = (JSONObject) parser.parse(new FileReader(caminhoArquivo));
		}
		catch(Exception e){
			TestBase.logReport(EnumFramework.Status.FAIL, "Erro ao recuperar o json: " + caminhoArquivo + ". Erro: " + e);
		}
		return jsonObject;
		
	}

	public static MobileConfiguration readMobileConfiguration(String path) throws FileNotFoundException {
		LogUtil.info(String.format("Lendo configuracao: %s",path));
		return new GsonBuilder().create().fromJson(new BufferedReader(new FileReader(path)), MobileConfiguration.class);
	}
}
