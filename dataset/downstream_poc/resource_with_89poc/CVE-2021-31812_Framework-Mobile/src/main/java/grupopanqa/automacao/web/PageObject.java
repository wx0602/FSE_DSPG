package grupopanqa.automacao.web;

import org.junit.Assert;
import org.openqa.selenium.Alert;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

/**
 * Classe responsavel por extender todas as classes de PageObject
 * 
 * @author 800041563
 *
 */
public class PageObject {

	protected int posicaoVertical = 0;
	protected WebDriver driver;
	protected Navegador navegador = null;

	/**
	 * Realiza a inicializacao dos elementos do pageobject
	 * 
	 * @param navegador
	 */
	public PageObject(Navegador navegador) {
		this.navegador = navegador;
		this.driver = navegador.getDriver();
		PageFactory.initElements(navegador.getDriver(), this);
	}

	/**
	 * Altera o frame da pagina
	 * 
	 * @param numFrame Index do frame a ser selecionado
	 * @param timeout  Tempo de timeout
	 */
	public Boolean alterarFrame(int numFrame, int timeout) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, timeout);
			wait.until(ExpectedConditions.frameToBeAvailableAndSwitchToIt(numFrame));
			return true;
		} catch (Exception e) {
			return false;
		}
	}

	/**
	 * Altera o frame da pagina
	 * 
	 * @param nomeFrame String Nome do frame a ser selecionado
	 * @param timeout  Tempo de timeout
	 */
	public Boolean alterarFrame(String nomeFrame, int timeout) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, timeout);
			wait.until(ExpectedConditions.frameToBeAvailableAndSwitchToIt(nomeFrame));
			return true;
		} catch (Exception e) {
			return false;
		}
	}
	
	/**
	 * Altera para o frame padrao
	 */
	public void retornarFramePadrao() {
		driver.switchTo().defaultContent();
	}

	/**
	 * Executa javascript
	 * 
	 * @param comando javascript
	 */
	public void executarJavaScript(String comando) {
		((JavascriptExecutor) driver).executeScript(comando);
	}
	
	/**
	 * Executa javascript retornando Int
	 * 
	 * @param comando javascript
	 * @return int 
	 */
	public int executarJavaScriptRetornaInt(String comando) {
		return ((Number)((JavascriptExecutor) driver).executeScript(comando)).intValue();
	}

	public void pageDown() {
		int alturaPaginaVisivel = executarJavaScriptRetornaInt("return window.innerHeight");
		posicaoVertical += alturaPaginaVisivel;
		executarJavaScript("window.scrollTo(0," + posicaoVertical + ")");
	}
	
	
	/**
	 * Retorna a quantidade de Scroll necessarios para percorrer a pagina web
	 * @return int Quantidade de Scroll necessario
	 */
	public int quantidadeScroll() {
		int contentHeight = executarJavaScriptRetornaInt("return window.innerHeight");
		int contentHeightTotal = executarJavaScriptRetornaInt("return document.body.scrollHeight");
		//double qtdScroll = (double) contentHeightTotal / contentHeight;
		//return (int) Math.ceil(qtdScroll);
		return contentHeightTotal/contentHeight;
	}

	/**
	 * Verifica se aparece um alert ate timeout
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return Boolean True - existe / False - não existe
	 */
	public Boolean verificaExistenciaAlertAposEspera(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.alertIsPresent());
			return true;
		} catch (Exception e) {
			return false;
		}
	}

	/**
	 * Confirmar alert
	 */
	public void confirmarAlert() {
		Alert alert = driver.switchTo().alert();
		alert.accept();
	}

	/**
	 * Cancelar alert
	 */
	public void cancelarAlert() {
		Alert alert = driver.switchTo().alert();
		alert.dismiss();
	}

	/**
	 * Recuperar texto do alert
	 * 
	 * @return
	 */
	public String recuperarTextoAlert() {
		String texto;
		Alert alert = driver.switchTo().alert();
		texto = alert.getText();
		return texto;
	}

	/**
	 * Aguardar execucao de javascript
	 */
	public void aguardarExecucaoJavaScript() {
		ExpectedCondition<Boolean> expectation = new ExpectedCondition<Boolean>() {
			public Boolean apply(WebDriver driver) {
				//System.out.println(((JavascriptExecutor) driver).executeScript("return document.readyState").toString());
				return ((JavascriptExecutor) driver).executeScript("return document.readyState").toString()
						.equals("complete");
			}
		};
		try {
			Thread.sleep(500);
			WebDriverWait wait = new WebDriverWait(driver, 30);
			wait.until(expectation);
		} catch (Throwable error) {
			Assert.fail("Timeout waiting for Page Load Request to complete.");
		}
	}

}
