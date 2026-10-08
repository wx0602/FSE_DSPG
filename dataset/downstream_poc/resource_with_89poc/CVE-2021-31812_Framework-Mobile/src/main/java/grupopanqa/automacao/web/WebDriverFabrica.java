package grupopanqa.automacao.web;

import grupopanqa.automacao.util.EnumFramework.Navegadores;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.Processos;
import grupopanqa.automacao.util.TestBase;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.ie.InternetExplorerDriver;
import org.openqa.selenium.remote.DesiredCapabilities;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

/**
 * Classe responsavel pela geracao de instancia de acordo com o tipo de
 * navegador
 * 
 * @author 800041563
 *
 */
public class WebDriverFabrica {

	static String diretorioExternoDriver = "C:/automacao_temp/";
	static String diretorioInternoJarDriver = "/resources/drivers/";
	static String diretorioInternoCodigoAbertoDriver = "/drivers/";
	static Boolean driverChromeCopiado = false;
	static Boolean driverIECopiado = false;
	static Boolean driverFirefoxCopiado = false;

	/**
	 * Cria instancia do navegador de acordo com o tipo informado
	 * 
	 * @param tipo do navegador
	 * @return WebDriver com o tipo de navegador escolhido
	 */
	@SuppressWarnings("deprecation")
	public WebDriver CriarInstancia(Navegadores tipo) {

		if (Navegadores.Chrome == tipo) {
			
			if(!driverChromeCopiado) {
				copiarDriverPastaExterna("chromedriver.exe");
				driverChromeCopiado = true;
			}
			ChromeOptions options = new ChromeOptions();
			options.addArguments("--disable-extensions");
			System.setProperty("webdriver.chrome.driver", diretorioExternoDriver + "chromedriver.exe");
			return new ChromeDriver(options);
		} else if (Navegadores.ChromeHeadLess == tipo) {
			
			if(!driverChromeCopiado) {
				copiarDriverPastaExterna("chromedriver.exe");
				driverChromeCopiado = true;
			}
			
			ChromeOptions options = new ChromeOptions();
			options.addArguments("--disable-extensions");
			options.addArguments("headless");
			options.addArguments("window-size=1200x600");
			System.setProperty("webdriver.chrome.driver", diretorioExternoDriver + "chromedriver.exe");

			return new ChromeDriver(options);
		} else if (Navegadores.IE == tipo) {
			
			if(!driverIECopiado) {
				copiarDriverPastaExterna("IEDriverServer.exe");
				driverIECopiado = true;
			}
			//parou de funcionar ao migrar appium 7 para 7.1 pom
			DesiredCapabilities options = DesiredCapabilities.internetExplorer();
			options.setCapability(InternetExplorerDriver.INTRODUCE_FLAKINESS_BY_IGNORING_SECURITY_DOMAINS, true);
			options.setCapability("nativeEvents", false);
			options.setCapability("ignoreZoomSetting", true);
			//options.setCapability("ignoreProtectedModeSettings", true);
			options.setCapability("requireWindowFocus", true);
			System.setProperty("webdriver.ie.driver", diretorioExternoDriver + "IEDriverServer.exe");
			return new InternetExplorerDriver(options);
		} else if (Navegadores.Firefox == tipo) {
			if(!driverFirefoxCopiado) {
				copiarDriverPastaExterna("geckodriver.exe");
				driverFirefoxCopiado = true;
			}
			return new FirefoxDriver();
		} else {
			return null;
		}
	}

	/**
	 * Realiza a extração do driver localizado dentro do framework (verificando se a execução e pela IDE ou pelo JAR
	 * @param nomeDriver Nome do driver a ser extraido
	 */
	public void copiarDriverPastaExterna(String nomeDriver) {

		try {

			// Finaliza todos os processos abertos do driver para que possa ser substituido
			// caso já exista
			Processos.finalizarProcesso(nomeDriver);

			// Atribui o driver localizado no framework para a variavel caso a execucao seja
			// atraves do JAR
			InputStream driverInterno = WebDriverFabrica.class
					.getResourceAsStream(diretorioInternoJarDriver + nomeDriver);
			
			
			// Caso seja atribuido null, significa que a execucao esta vindo atraves de uma
			// IDE (codigo fonte)
			if (driverInterno == null) {
				//System.out.println("Execução através da IDE");
				driverInterno = WebDriverFabrica.class.getResourceAsStream(diretorioInternoCodigoAbertoDriver + nomeDriver);
			}

			//Cria o diretorio onde sera colocado o driver caso nao exista
			File caminhoExternoDriver = new File(diretorioExternoDriver);
			if (!caminhoExternoDriver.isDirectory()) {
				caminhoExternoDriver.mkdirs();
			}

			//Realiza a extracao do Driver para o diretorio externo
			FileOutputStream driverExterno = new FileOutputStream(diretorioExternoDriver + nomeDriver);
			byte bytes[] = new byte[1000];
			int k = 0;
			while ((k = driverInterno.read(bytes)) != -1) {
				driverExterno.write(bytes, 0, k);
			}
			
			driverInterno.close();
			driverExterno.close();

		} catch (Exception e) {
			e.printStackTrace();
			TestBase.logReport(Status.FAIL, "Erro ao copiar o driver para fora do framework. Erro: " + e);
		}

	}

}
