package grupopanqa.automacao.mobile;

import grupopanqa.automacao.config.ParametersConfiguration;
import grupopanqa.automacao.mobile.config.data.DeviceConfigurationModel;
import grupopanqa.automacao.mobile.config.data.MobileConfiguration;
import grupopanqa.automacao.mobile.services.ExecutionSideService;
//import grupopanqa.automacao.mobile.services.LogEventListener;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.PropriedadeSistema;
import io.appium.java_client.AppiumDriver;
import io.appium.java_client.MobileElement;
import io.appium.java_client.events.EventFiringWebDriverFactory;
import io.appium.java_client.remote.AndroidMobileCapabilityType;
import io.appium.java_client.remote.IOSMobileCapabilityType;
import org.openqa.selenium.SessionNotCreatedException;
import org.openqa.selenium.remote.DesiredCapabilities;

import static grupopanqa.automacao.config.ParametersConfiguration.APPIUM_SERVER_ADDRESS;

import java.net.MalformedURLException;
import java.net.URL;

/**
 * Classe responsavel pela geracao de instancia do device
 * 
 * @author 800041563
 *
 */
public class MobileDriverFabrica {

	Appium appium; // Instancia para inicializar e finalizar o server
	AppiumDriver<MobileElement> driverGenerico = null;

	String localAppiumJS = ConfigMobile.getLocalAppium();
	String localNodeExe = ConfigMobile.getLocalNode();
	String browserstack_user_name = ConfigMobile.getBrowserstackUsuario();
	static String browserstack_access_key = ConfigMobile.getBrowserstackAccessKey();
	String servidorIp = ConfigMobile.getServidorIp();
	String portaInicial = ConfigMobile.getPortaInicialServidor();
	String localCaCertificados = ConfigMobile.getLocalCaCertificados();
	String senhaCaCertificados = ConfigMobile.getSenhaCaCertificados();
	String thread_id;
	int porta;
	URL appiumServerURL;
	DesiredCapabilities dc;
	ExecutionSideService sideService;
	//static Local l = new Local();

	/**
	 * Cria instancia do device (tambem inicia o Appium, e no caso de ser
	 * BrowserStack, tambem realiza a conexao local )
	 * 
	 * @return AppiumDriver Instancia do device
	 * @throws MalformedURLException 
	 */
	public AppiumDriver<MobileElement> CriarInstancia() throws MalformedURLException {
		
		//Pega o id da thread para usar como valor único da execução (auxilia no vínculo do device reservado à thread e porta (appium e browserstack)
		String thread_id = String.valueOf(Thread.currentThread().getId());
		porta = Integer.valueOf(portaInicial + thread_id);
		//porta = 2814;
		//Realiza a inicialização do Appium pelo node utilizando a porta informada
		appiumServerURL = new URL(APPIUM_SERVER_ADDRESS.value());

		//Recebe o primeiro (0) device disponível para ser utilizado
		dc = ControleDeviceCapabilities.getDeviceDisponivel(0);
		TestBaseMobile.logReport(Status.INFO, "Capabilities selecionado para o teste: " + dc.toString());
		String plataforma = ConfigMobile.getPlataforma();
		System.out.println(plataforma);
		
		//Capabilities especificos para cada tipo de plataforma
		if (plataforma.equals("android")) {
			// Informado uma porta diferente da passada para o Appium
			dc.setCapability(AndroidMobileCapabilityType.SYSTEM_PORT, porta + 10);
			dc.setCapability(AndroidMobileCapabilityType.ACCEPT_INSECURE_CERTS, true);
			dc.setCapability(AndroidMobileCapabilityType.ACCEPT_SSL_CERTS, true);
			dc.setCapability(AndroidMobileCapabilityType.AUTO_GRANT_PERMISSIONS, true);
		}
		else if(plataforma.equals("ios")) {
			dc.setCapability(IOSMobileCapabilityType.AUTO_ACCEPT_ALERTS, true);
		}
		
		
		dc.setCapability("newCommandTimeout", 500);
		
		// Caso o device seja da browserstack, é necessario realizar o apontamento do
		// cacert que contem o certificado da BS, alem de realizar a conexao local com a BS 
		// para que o device tenha acesso à rede interna
		if (ConfigMobile.getTipoDevice().equals("browserstack_device")) {
			PropriedadeSistema.definirCaCerts(localCaCertificados);
			//Verifica se a conexão será local
			if (ConfigMobile.getBrowserstackLocal().equals("true")) {
				BrowserStackLocal bsLocal = new BrowserStackLocal(browserstack_user_name, browserstack_access_key);
				bsLocal.conectaBrowserstackLocal(thread_id);
			}
			dc.setCapability("browserstack.localIdentifier", thread_id);
			try {
//				driverGenerico = new AppiumDriver<MobileElement>(linkBS, dc);
			} catch (SessionNotCreatedException erro) {
				//Caso apresente erro de certificado, é realizado procedimento para baixar e adicionar o certificado da browserstack no CaCerts
				//Em seguida é realizado nova tentativa de conexão
				//TODO: Validar importacao certificado da nuvem para jvm
				//CaCertificado.adicionaPermissao(linkBS.toString(), localCaCertificados, senhaCaCertificados);
//				driverGenerico = new AppiumDriver<MobileElement>(linkBS, dc);
			}
			//Caso o device seja físico ou emulado
		}

		//Chama servico auxiliar para execuçao de métodos antes da instancia do WebDriver ser criada
		sideService.beforeDriver();

		//Pegar capabilities do servico auxiliar
		dc.merge(sideService.generateCapabilities());

		driverGenerico = new AppiumDriver<MobileElement>(appiumServerURL, dc);

		//Chama servico auxiliar para execuçao de métodos apos da instancia do WebDriver ser criada
		sideService.afterDriver(driverGenerico);
		return driverGenerico;
	}

	public AppiumDriver<MobileElement> buildDriver(URL serverURL, MobileConfiguration configuration, DeviceConfigurationModel selectedDevice, ExecutionSideService sideService) throws MalformedURLException {
		DesiredCapabilities capabilities = new DesiredCapabilities();
		this.sideService = sideService;
		//Merge de capabilities gerais
		capabilities.merge(configuration.getGeneralCapabilities());
		//Merge de capabilities do app
		capabilities.merge(configuration.getApp().getApplicationCapabilities());
		//Merge de capabilities do device
		capabilities.merge(selectedDevice.getDeviceCapabilities());

		//Chama o servico auxiliar antes do driver ser criado
		sideService.beforeDriver();

		//Pegar capabilities do servico auxiliar
		capabilities.merge(sideService.generateCapabilities());

		AppiumDriver driver = new AppiumDriver<MobileElement>(serverURL, capabilities);

		//Chama servico auxiliar para execuçao de métodos apos da instancia do WebDriver ser criada
		sideService.afterDriver(driver);
		this.driverGenerico = driver;
		return this.driverGenerico;
	}


	public void liberarInstancia() {
		// Fecha o aplicativo
		driverGenerico.closeApp();
		// Fecha a instancia com o device
		driverGenerico.quit();
		// Libera o device da lista estatica para ficar disponivel para o proximo teste
		ControleDeviceCapabilities.liberaDevice(dc);
		// Finaliza o appium
		//appium.finalizarInstancia();
		sideService.stop();
	}

}
