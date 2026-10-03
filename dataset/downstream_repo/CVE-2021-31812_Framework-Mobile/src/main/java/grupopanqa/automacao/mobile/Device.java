package grupopanqa.automacao.mobile;

import static grupopanqa.automacao.config.ParametersConfiguration.APPIUM_SERVER_ADDRESS;
import static grupopanqa.automacao.config.ParametersConfiguration.DEVICE_IOS_JSON;
import static grupopanqa.automacao.config.ParametersConfiguration.DEVICE_JSON;
import static grupopanqa.automacao.config.ParametersConfiguration.RUNTIME_ENVIRONMENT;
import static grupopanqa.automacao.config.RuntimeEnvironmentType.valueOf;
import static grupopanqa.automacao.mobile.ConfigMobile.ifAndroid;
import static grupopanqa.automacao.mobile.services.ExecutionSideServiceFactory.createInstance;
import static grupopanqa.automacao.util.Arquivo.readMobileConfiguration;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.openqa.selenium.mobile.NetworkConnection;
import org.openqa.selenium.mobile.NetworkConnection.ConnectionType;

import grupopanqa.automacao.config.ParametersConfiguration;
import grupopanqa.automacao.config.RuntimeEnvironmentType;
import grupopanqa.automacao.dados.ConfiguracaoDados;
import grupopanqa.automacao.mobile.config.data.DeviceConfigurationModel;
import grupopanqa.automacao.mobile.config.data.MobileConfiguration;
import grupopanqa.automacao.mobile.services.ExecutionSideService;
import grupopanqa.automacao.mobile.services.ExecutionSideServiceFactory;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.TestBase;
import io.appium.java_client.AppiumDriver;

/**
 * Classe responsavel por controlar o device
 * @author 800041563
 *
 */
public class Device {
	private AppiumDriver<?> appiumDriver = null;
	MobileDriverFabrica webDriverFabrica;

	/**
	 * Inicia o device
	 */
	@Deprecated
	public Device() {
		try {
			webDriverFabrica = new MobileDriverFabrica();
			appiumDriver = webDriverFabrica.CriarInstancia();
		} catch (MalformedURLException erro) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Erro ao iniciar device: " + erro);
		}
	}

	/**
	 * Inicia o device
	 */
	public Device(String testName) {
		try {
			String.format("Iniciando o teste %s", testName);
			System.out.println("Iniciando o teste");
			
			webDriverFabrica = new MobileDriverFabrica();

			//Pegar a url de execucao dos argumentos
			URL url = new URL(APPIUM_SERVER_ADDRESS.value());
			
			ParametersConfiguration jsonCaps = ifAndroid(()-> DEVICE_JSON, ()-> DEVICE_IOS_JSON);
			
			MobileConfiguration configuration = readMobileConfiguration(jsonCaps.value());

			//Procura o device selecionado na lista de devices
			DeviceConfigurationModel selectedDevice = selectDevice(configuration.getDevices());

			//Constroi servico auxiliar
			ExecutionSideService executionSideService = createInstance(valueOf(RUNTIME_ENVIRONMENT.value()), configuration.getSideService());

			//Constroi o driver
			appiumDriver = webDriverFabrica.buildDriver(url, configuration,  selectedDevice, executionSideService);

		} catch (MalformedURLException erro) {
			TestBase.logReport(Status.FAIL, "Erro ao iniciar device: " + erro);
		} catch (FileNotFoundException e) {
			TestBase.logReport(Status.FAIL, "Erro ao carregar arquivo de configuracao: " + e);
		}
	}

	/**
	 * Seleciona o device informado na lista
	 * @param devices lista de devices configurados
	 * @param deviceId id do device desejado
	 * @return device selecionado
	 */
	private DeviceConfigurationModel selectDevice(List<DeviceConfigurationModel> devices, String deviceId) {
		Optional<DeviceConfigurationModel> optionalDeviceConfigurationModel = devices.stream()
				.filter(deviceConfigurationModel -> deviceId.equals(deviceConfigurationModel.getId()))
				.findFirst();
		if(!optionalDeviceConfigurationModel.isPresent()){
			throw new RuntimeException(String.format("Device %s nao encontrado",deviceId));
		}
		return optionalDeviceConfigurationModel.get();
	}

	/**
	 * Seleciona o device informado na lista
	 * @param devices lista de devices configurados
	 * @return device selecionado
	 */
	private DeviceConfigurationModel selectDevice(List<DeviceConfigurationModel> devices) {
		Optional<DeviceConfigurationModel> optionalDeviceConfigurationModel = devices.stream().findFirst();
		return optionalDeviceConfigurationModel.get();
	}


	public void ativarModoAviao() {
		NetworkConnection mobileDriver = (NetworkConnection) appiumDriver;
		 if (mobileDriver.getNetworkConnection() != ConnectionType.AIRPLANE_MODE) {
		   // enabling Airplane mode
		   mobileDriver.setNetworkConnection(ConnectionType.AIRPLANE_MODE);
		 }
	}
	

	/**
	 * Finaliza a conexão e o driver
	 */
	public void finalizar() {
		webDriverFabrica.liberarInstancia();
	}	
	
	/**
	 * Recupera o driver
	 * @return AppiumDriver
	 */
	public AppiumDriver<?> getDriver(){
		return appiumDriver;
	}
	
	/**
	 * Classe responsavel por listar todos os devices conectados no computador
	 * @return List<String> Lista dos Ids dos devices
	 */
	public static List<String> listarDevicesConectados() {

		List<String> listaDeviceId = new ArrayList<String>();

		try {
			String commandString = String.format("%s", "adb devices");

			Runtime rt = Runtime.getRuntime();
			Process process = rt.exec(commandString);
			BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
			String line;

			while ((line = reader.readLine()) != null) {
				if (!line.contains("List") && line.contains("device")) {
					String id = line.substring(0, line.indexOf("\t"));
					listaDeviceId.add(id);
				}
				;
			}
		} catch (IOException erro) {
			erro.printStackTrace();
			TestBase.logReport(Status.FAIL, "Falha na validação de devices disponíveis. Erro: " + erro);
		}
		return listaDeviceId;
	}
	
}
