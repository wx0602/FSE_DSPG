package grupopanqa.automacao.dados;

import static grupopanqa.automacao.mobile.ConfigMobile.getPlataforma;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.Properties;

import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.TestBase;

/**
 * Classe com metodos relacionados a configuracao da execucao/ambiente. Baseado em Variaveis de ambiente e arquivos Properties
 * @author 800041563
 *
 */
public class ConfiguracaoDados {
	
	static Properties properties;
	private final String propertyFilePath= "src//test//resources//Configuration.properties";

	/**
	 * Realiza a leitura do arquivo 
	 * @param configFile - Caminho do arquivo properties caso não esteja no local padrao (variavel propertyFilePath)
	 * @throws IOException 
	 */
	public ConfiguracaoDados(String configFile) throws IOException{
		if ("".equals(configFile)){
			carregarProperties(propertyFilePath);
		}
		else{
			carregarProperties(configFile);
		}
		
	}
	
	/**
	 * Realiza a leitura do arquivo (localizado no local padrao)
	 * @throws IOException
	 */
	public ConfiguracaoDados(){
		try {
			carregarProperties(propertyFilePath);
		} catch (IOException erro) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Falha ao tentar carregar arquivo properties. Erro: " + erro);
		}
	}
	
	/**
	 * Carrega os valores do arquivo Properties
	 * @param configFile Caminho do arquivo Properties
	 * @throws IOException 
	 */
	public void carregarProperties(String configFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(configFile));	
			
		properties = new Properties();

		properties.load(reader);
		
		reader.close();
	}
	
	public static String recuperarValor(String chave) {
		return recuperarValor(chave, null);
	}
	
	/**
	 * Retorna o valor referente a chave informada por parametro do Properties ou Variavel de Ambiente
	 * @param chave Chave a ser consultado o valor
	 * @return String Value da chave
	 */
	public static String recuperarValor(String chave, String valorPadrao) {
		String varAmbiente = System.getProperty(chave); // VariavelAmbiente.pb.environment().get(chave);

		if(varAmbiente != null && !varAmbiente.trim().isEmpty()) return varAmbiente;
		
		String varProperty = properties.getProperty(chave);
		
		if(varProperty != null && !varProperty.trim().isEmpty()) return varProperty;

		if (valorPadrao != null) return valorPadrao;
		
		throw new RuntimeException("Valor de Input solicitado: " + chave + " não foi encontrado no arquivo de Properties e Variável de Ambiente");
	}
	
	public static String getReportPath() {
		return recuperarValor("REPORT_PATH") + getPlataforma() + "/";
	}
	
	/**
	 * Atualiza o valor informado pelo valor da massa de dados (configProperties ou variavel de ambiente)
	 * @param valor Valor a ser atualizado
	 * @param delimitadorInicio Delimitador que mostra aonde comeca o trecho que deve ser substituido
	 * @param delimitadorFim Delimitador que mostra aonde termina o trecho que deve ser substituido
	 * @param configFileMassa Arquivo de Massa aonde deve ser consultado o valor
	 * @return String Valor atualizado com os dados da massa
	 * @throws IOException 
	 */
	public static String atualizarValorMassa(String valor, String delimitadorInicio, String delimitadorFim, String configFileMassa) throws IOException{
		ConfiguracaoDados configFile = new ConfiguracaoDados(configFileMassa);		
		while (valor.contains(delimitadorInicio)){
			int pos1 = valor.indexOf(delimitadorInicio);
			int pos2 = valor.indexOf(delimitadorFim);
			String paramComChave = valor.substring(pos1, pos2 + delimitadorFim.length());
			String param = paramComChave.replace(delimitadorInicio, "").replace(delimitadorFim, "");
			String paramValor = configFile.recuperarValor(param);
			valor = valor.replace(paramComChave, paramValor);
		}
		return valor;
	}
	public static String atualizarValorMassa(String valor, String delimitadorInicio, String delimitadorFim) throws IOException{
		return atualizarValorMassa(valor, delimitadorInicio, delimitadorFim, "");
	}
	public static String atualizarValorMassa(String valor) throws IOException{
		return atualizarValorMassa(valor, "{{", "}}", "");
	}

}