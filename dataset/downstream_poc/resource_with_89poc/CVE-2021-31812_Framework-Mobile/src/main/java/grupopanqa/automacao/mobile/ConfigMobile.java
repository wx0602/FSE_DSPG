package grupopanqa.automacao.mobile;

import grupopanqa.automacao.config.ParametersConfiguration;
import grupopanqa.automacao.dados.ConfiguracaoDados;
import grupopanqa.automacao.mobile.config.data.MobileConfiguration;
import grupopanqa.automacao.util.Arquivo;

import java.util.function.Supplier;

import org.json.JSONObject;

/**
 * Classe responsável por centralizar, gerenciar e disponibilizar todas as informações do arquivo de configuração (padrão device.json)
 * @author 800041563
 *
 */
public class ConfigMobile {

	private static JSONObject jsonConfig;
	private static String plataforma;
	private static String tipoDevice;
	private static String diretorioReport;
	private static String ambiente;
	private static String servidorIp;
	private static String portaInicialServidor;
	private static String browserstackUsuario;
	private static String browserstackAccessKey;
	private static String browserstackLocal;
	private static String localAppium;
	private static String localNode;
	private static String localCaCertificados;
	private static String senhaCaCertificados;
	private static JSONObject devicesCapabilities;

	//Chaves de consulta do arquivo json
	private static final String CONFIG_KEY_DEVICE_TYPES = "device_types";
	private static final String CONFIG_KEY_AMBIENTE = "ambiente";
	private static final String CONFIG_KEY_DEVICE_HABILITADO = "device_habilitado";
	private static final String CONFIG_KEY_DIRETORIO_REPORT = "diretorio_report";
	private static final String CONFIG_KEY_CAPABILITIES = "capabilities";
	private static final String CONFIG_KEY_BROWSERSTACK_USUARIO = "browserstack_usuario";
	private static final String CONFIG_KEY_BROWSERSTACK_ACCESS_KEY = "browserstack_access_key";
	private static final String CONFIG_KEY_BROWSERSTACK_LOCAL = "browserstack.local";
	private static final String CONFIG_KEY_IP_SERVIDOR = "ip_servidor";
	private static final String CONFIG_KEY_PORTA_INICIAL_SERVIDOR = "porta_inicial_servidor";
	private static final String CONFIG_KEY_BROWSERSTACK_DEVICE = "browserstack_device";
	private static final String CONFIG_KEY_LOCAL_APPIUM = "local_appium";
	private static final String CONFIG_KEY_LOCAL_NODE = "local_node";
	private static final String CONFIG_KEY_LOCAL_CA_CERTIFICADOS = "local_ca_certificados";
	private static final String CONFIG_KEY_SENHA_CA_CERTIFICADOS = "senha_ca_certificados";
	
	private static Boolean carregado = false;// Verifica se o arquivo já foi carregado (será carregado apenas uma vez)

	public synchronized static void carregaArquivo(String caminhoArquivo) {
		
		if (!carregado) {
			//Carrega todo o arquivo json
			jsonConfig = new JSONObject(Arquivo.retornarTexto(caminhoArquivo));

			//Carrega todas as variáveis com os dados do jsonConfig
			ambiente = jsonConfig.get(CONFIG_KEY_AMBIENTE).toString();
			localAppium = jsonConfig.get(CONFIG_KEY_LOCAL_APPIUM).toString();
			localNode = jsonConfig.get(CONFIG_KEY_LOCAL_NODE).toString();
			localCaCertificados = jsonConfig.get(CONFIG_KEY_LOCAL_CA_CERTIFICADOS).toString();
			senhaCaCertificados = jsonConfig.get(CONFIG_KEY_SENHA_CA_CERTIFICADOS).toString();
			tipoDevice = jsonConfig.get(CONFIG_KEY_DEVICE_HABILITADO).toString();
			diretorioReport = jsonConfig.get(CONFIG_KEY_DIRETORIO_REPORT).toString();
			servidorIp = jsonConfig.get(CONFIG_KEY_IP_SERVIDOR).toString();
			portaInicialServidor = jsonConfig.get(CONFIG_KEY_PORTA_INICIAL_SERVIDOR).toString();
			devicesCapabilities = jsonConfig.getJSONObject(CONFIG_KEY_DEVICE_TYPES).getJSONObject(plataforma)
					.getJSONObject(tipoDevice).getJSONObject(CONFIG_KEY_CAPABILITIES);
			//Carrega dados apenas se a execução for para o browserstack
			if (tipoDevice.equals(CONFIG_KEY_BROWSERSTACK_DEVICE)) {
				browserstackUsuario = jsonConfig.getJSONObject(CONFIG_KEY_DEVICE_TYPES).getJSONObject(plataforma)
						.getJSONObject(CONFIG_KEY_BROWSERSTACK_DEVICE).get(CONFIG_KEY_BROWSERSTACK_USUARIO).toString();
				browserstackAccessKey = jsonConfig.getJSONObject(CONFIG_KEY_DEVICE_TYPES).getJSONObject(plataforma)
						.getJSONObject(CONFIG_KEY_BROWSERSTACK_DEVICE).get(CONFIG_KEY_BROWSERSTACK_ACCESS_KEY)
						.toString();
				browserstackLocal = jsonConfig.getJSONObject(CONFIG_KEY_DEVICE_TYPES).getJSONObject(plataforma)
						.getJSONObject(CONFIG_KEY_BROWSERSTACK_DEVICE).getJSONObject(CONFIG_KEY_CAPABILITIES).get(CONFIG_KEY_BROWSERSTACK_LOCAL)
						.toString();
			}
			//Monta a lista de devices (capabilities) para disponibilizar para uso
			ControleDeviceCapabilities.montaListaDeviceCapabilities(devicesCapabilities);
			
			//Seta true para que os dados não sejam carregados novamente
			carregado = true;
		}

	}

	public synchronized static void carregaConfig(MobileConfiguration configuration) {

		if (!carregado) {
			//Carrega todas as variáveis com os dados do jsonConfig
			ambiente = configuration.getAmbiente().name().toLowerCase();
			localAppium = "";
			localNode =  "";
			localCaCertificados =  "";
			senhaCaCertificados =  "";
			//tipoDevice = configuration.getDevices().stream().filter(deviceConfigurationModel -> ParametersConfiguration.DEVICE_ID.value().equals(deviceConfigurationModel.getId())).findFirst().get().getType().name();
			tipoDevice = configuration.getDevices().stream().findFirst().get().getType().name();
			servidorIp = ParametersConfiguration.APPIUM_SERVER_ADDRESS.value();
			portaInicialServidor = "";
			devicesCapabilities= new JSONObject("{}");
			//Seta true para que os dados não sejam carregados novamente
			carregado = true;
		}

	}

	public static String getPlataforma() {
		return ConfiguracaoDados.recuperarValor("PLATAFORMA");
	}
	
	public static boolean isAndroid() {
		return getPlataforma().equals("android");
	}
	
	public static boolean isIos() {
		return getPlataforma().equals("ios");
	}
	
	public static void ifIos(Runnable runnable) {
		if (isIos()) runnable.run();
	}
	
	public static void ifAndroid(Runnable runnable) {
		if (isAndroid()) runnable.run();
	}
	
	public static <T> T ifAndroid(Supplier<T> runnable) {
		if (isAndroid()) return runnable.get();
		
		return null;
	}
	
	public static void ifAndroid(Runnable runnableIf, Runnable runnableElse) {
		if (isAndroid()) runnableIf.run();
		else runnableElse.run();
	}
	
	public static <T> T ifAndroid(Supplier<T> runnableIf, Supplier<T> runnableElse) {
		if (isAndroid()) return runnableIf.get();
		else return runnableElse.get();
	}
	
	public static void ifIos(Runnable runnableIf, Runnable runnableElse) {
		if (isIos()) runnableIf.run();
		else runnableElse.run();
	}

	public static String getDiretorioReport() {
		return diretorioReport;
	}

	public static String getTipoDevice() {
		return tipoDevice;
	}

	public static String getServidorIp() {
		return servidorIp;
	}

	public static String getPortaInicialServidor() {
		return portaInicialServidor;
	}

	public static String getBrowserstackUsuario() {
		return browserstackUsuario;
	}

	public static String getBrowserstackAccessKey() {
		return browserstackAccessKey;
	}

	public static String getBrowserstackLocal() {
		return browserstackLocal;
	}
	
	public static String getLocalAppium() {
		return localAppium;
	}

	public static String getLocalNode() {
		return localNode;
	}

	public static String getLocalCaCertificados() {
		return localCaCertificados;
	}
	public static String getSenhaCaCertificados() {
		return senhaCaCertificados;
	}
	public static String getAmbiente() {
		return ambiente;
	}

}