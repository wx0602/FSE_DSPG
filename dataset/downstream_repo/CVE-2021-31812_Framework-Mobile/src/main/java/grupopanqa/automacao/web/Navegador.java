package grupopanqa.automacao.web;

import grupopanqa.automacao.util.EnumFramework.Navegadores;
import org.openqa.selenium.WebDriver;

/**
 * Classe responsavel por controlar o navegador
 * @author 800041563
 *
 */
public class Navegador {
	private WebDriver webDriver = null;

	/**
	 * Inicia o navegador
	 * @param tipo Tipo de navegador (IE, Edge, Chrome, Firefox...)
	 */
	public Navegador(Navegadores tipo) {
		WebDriverFabrica webDriverFabrica = new WebDriverFabrica();
		webDriver = webDriverFabrica.CriarInstancia(tipo);
	}

	/**
	 * Acessa a pagina informada
	 * @param url URL da pagina
	 */
	public void acessarPaginaWeb(String url) {
		webDriver.get(url);
	}

	/**
	 * Altera a janela utilizada
	 */
	public void alterarJanelaNavegador(String nomeJanela) {
		webDriver.switchTo().window(nomeJanela);
	}
	
	/**
	 * Atualiza a pagina atual
	 */
	public void atualizarPaginaWeb() {
		webDriver.navigate().to(webDriver.getCurrentUrl());
	}
	
	/**
	 * Maximiza a janela do navegador
	 */
	public void maximizar() {
		webDriver.manage().window().maximize();
	}
	
	/**
	 * Finaliza o navegador e o driver
	 */
	public void finalizar() {
		webDriver.close();
		webDriver.quit();
	}	
	
	/**
	 * Recupera o driver
	 * @return WebDriver
	 */
	public WebDriver getDriver(){
		return webDriver;
	}
	
}
