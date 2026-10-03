package grupopanqa.automacao.mobile;

import grupopanqa.automacao.util.EnumFramework.AtributoMobile;
import grupopanqa.automacao.util.EnumFramework.Status;
import io.appium.java_client.AppiumDriver;
import io.appium.java_client.MobileBy;
import io.appium.java_client.MobileElement;
import io.appium.java_client.TouchAction;
import io.appium.java_client.touch.offset.PointOption;

import static grupopanqa.automacao.mobile.TestBaseMobile.logReport;

import org.openqa.selenium.By;
import org.openqa.selenium.Dimension;
import org.openqa.selenium.InvalidElementStateException;
import org.openqa.selenium.Point;
import org.openqa.selenium.StaleElementReferenceException;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

/**
 * Classe com metodos do elemento mobile
 * 
 * @author 800041563
 *
 */
public class ElementoMobile {

	protected MobileElement elemento;
	private AppiumDriver<?> driver;
	private By elementoLocator;
	private AtributoMobile atributoElemento;
	private String valorElemento;
	private Device device;

	// quando o indexElemento é diferente de -1, quer dizer que o elemento se trata
	// de uma lista de elementos e o index é a posicao
	// a ser utilizada
	private int indexElemento = -1;

	/**
	 * Construtor do elemento
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param driver
	 */
	public ElementoMobile(AtributoMobile atributo, String valor, Device device) {
		this.device = device;
		this.driver = device.getDriver();
		atributoElemento = atributo;
		valorElemento = valor;
		elementoLocator = montarLocator(atributo, valor);
	}

	public String getValorElemento() {
		
		return valorElemento;
		
	}

	
	/**
	 * Construtor utilizado quando o elemento é instanciado pelo ElementosWeb (lista
	 * de elementos)
	 * 
	 * @param elementosWeb Lista de elementos web
	 * @param index        Posição do elemento da lista
	 */
	public ElementoMobile(ElementosMobile elementosMobile, int index) {
		driver = elementosMobile.getDriver();
		indexElemento = index;
		valorElemento = elementosMobile.getValorElemento();
		atributoElemento = elementosMobile.getAtributoElemento();
		elementoLocator = montarLocator(atributoElemento, valorElemento);
	}

	public MobileElement getMobileElement() {
		if (elemento == null) {
			localizarElemento();
		}
		return elemento;
	}

	/**
	 * Atualiza o valor do locator
	 * 
	 * @param valorAntigo Texto a ser substituído
	 * @param valorNovo   Novo texto a ser inserido no lugar
	 */
	public ElementoMobile atualizarValorLocator(String valorAntigo, String valorNovo) {
		valorElemento = valorElemento.replace(valorAntigo, valorNovo);
		elementoLocator = montarLocator(atributoElemento, valorElemento);
		return this;
	}

	/**
	 * Override do toString para quando o elemento Locator for null (ex: quando vier
	 * de uma lista), realizar o retorno do texto próprio elemento
	 */
	@Override
	public String toString() {
		if (elementoLocator == null) {
			return elemento.toString();
		} else {
			return elementoLocator.toString();
		}
	}

	/**
	 * Metodo para buscar o elemento mobile no aplicativo
	 * 
	 * @return ElementoMobile Retorna o elemento mobile
	 */
	public ElementoMobile localizarElemento() {
		if (verificarElementoExiste()) {
			// Verifica se o elemento a ser utilizado é único ou veio de uma lista - nesse
			// caso é utilizado o index
			if (atributoElemento == AtributoMobile.Predicate){
				elemento = (MobileElement) driver.findElement(MobileBy.iOSNsPredicateString(valorElemento));
			}
			if (atributoElemento == AtributoMobile.AccessibilityId){
				elemento = (MobileElement) driver.findElement(MobileBy.AccessibilityId(valorElemento));
			}
			if (indexElemento == -1) {
				elemento = (MobileElement) driver.findElement(elementoLocator);
			} else {
				elemento = (MobileElement) driver.findElements(elementoLocator).get(indexElemento);

			}
		} else {
			TestBaseMobile.logReport(Status.FAIL, "Elemento nao encontrado: " + this.toString(), true, device);
		}
		return this;
	}

	/**
	 * Metodo para retornar quantidades de elementos encontrados na pagina
	 * 
	 * @return int quantidade de elementos
	 */
	public int contadorElementos() {
		int contador = driver.findElements(elementoLocator).size();
		return contador;
	}

	/**
	 * Metodo para verificar se existe o elemento mobile no aplicativo
	 * 
	 * @return Boolean Retorna true se existe o elemento
	 */
	public Boolean verificarElementoExiste() {
		if (contadorElementos() > 0) {
			return true;
		} else {
			return false;
		}
	}
	
	/**
	 * Metodo para verificar se existe o elemento mobile no aplicativo com timeout
	 * 
	 * @param tempoEsperaSegundos
	 * @return Boolean Retorna true se existe o elemento
	 */
	public Boolean verificarElementoExiste(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.presenceOfElementLocated(elementoLocator));
			return true;
		} catch (Exception e) {
			return false;
		}

	}

	/**
	 * Realiza o click no elemento
	 * 
	 * @return ElementoMobile
	 */
	public ElementoMobile clicar() {
		if (elemento == null) localizarElemento();
		
		try {
			elemento.click();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.click();
		} catch (Exception e) {
			logReport(Status.FAIL, "Erro ao clicar no elemento: " + this.toString() + ". Erro: " + e, true, device);
		}
		
		logReport(Status.INFO, "Realizado click no elemento: " + this.toString(), false, device);
		
		return this;
	}
	
	public ElementoMobile clicarPorPosicao() {
		if (elemento == null) localizarElemento();
		
		try {
			clickByPosition();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			clickByPosition();
		} catch (Exception e) {
			logReport(Status.FAIL, "Erro ao clicar no elemento: " + this.toString() + ". Erro: " + e, true, device);
		}
		
		logReport(Status.INFO, "Realizado click no elemento: " + this.toString(), false, device);
		
		return this;
	}
	
	private void clickByPosition() {
		Point location = elemento.getLocation();
		Dimension size = elemento.getSize();
		
		PointOption<?> pointOption = new PointOption<>();
		pointOption.withCoordinates(location.x + (size.width / 2), location.y + (size.height / 2));
		
		TouchAction<?> touchAction = new TouchAction<>(driver);
		touchAction.press(pointOption).perform();
	}

	/**
	 * Recupera o texto do elemento mobile
	 * 
	 * @return String Texto do elemento
	 */
	public String recuperarTexto() {
		if (elemento == null)
			localizarElemento();
		String texto = "";
		try {
			texto = elemento.getText();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			texto = elemento.getText();
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao recuperar texto do elemento: " + this.toString() + ". Erro: " + e, true, device);
		}
		return texto;
	}

	/**
	 * Recupera o atributo do elemento mobile
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @return String Valor do atributo do elemento
	 */
	public String recuperarAtributoElemento(String atributo) {
		if (elemento == null)
			localizarElemento();

		String valorAtributo = "";

		try {
			valorAtributo = elemento.getAttribute(atributo);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			valorAtributo = elemento.getAttribute(atributo);
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao recuperar atributo '" + atributo + "' do elemento: " + this.toString() + ". Erro: " + e,
					true, device);
		}

		return valorAtributo;
	}

	/**
	 * Realiza a digitacao de texto no elemento mobile
	 * 
	 * @param texto String a ser digitado
	 * @return ElementoMobile
	 */
	public ElementoMobile digitar(String texto) {
		
		if (elemento == null)
			localizarElemento();
		try {
			elemento.sendKeys(texto);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.sendKeys(texto);
		} catch (InvalidElementStateException e) {
			elemento.findElementByClassName("android.widget.EditText").sendKeys(texto);

		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao digitar o texto '" + texto + "' no elemento: " + this.toString() + ". Erro: " + e, true,
					device);
		}
		TestBaseMobile.logReport(Status.INFO, "Digitado texto: " + texto + " no elemento: " + this.toString(), false,
				device);
		return this;
	}

	/**
	 * Realiza a digitacao de texto no elemento mobile
	 * 
	 * @param texto String a ser digitado
	 * @return ElementoMobile
	 */
	public ElementoMobile digitarViaKeyboard(String texto) {
		
		if (elemento == null)
			localizarElemento();
		try {
			elemento.click();
			driver.getKeyboard().pressKey(texto);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			driver.getKeyboard().pressKey(texto);
		} catch (InvalidElementStateException e) {
			elemento.findElementByClassName("android.widget.EditText");
			localizarElemento();
			driver.getKeyboard().pressKey(texto);

		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao digitar o texto '" + texto + "' no elemento: " + this.toString() + ". Erro: " + e, true,
					device);
		}
		TestBaseMobile.logReport(Status.INFO, "Digitado texto: " + texto + " no elemento: " + this.toString(), false,
				device);
		return this;
	}
	
	/**
	 * Realiza a limpeza do elemento (retira texto do elemento caso possua)
	 * 
	 * @return ElementoMobile
	 */
	public ElementoMobile limparTexto() {
		if (elemento == null)
			localizarElemento();

		try {
			elemento.clear();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.clear();
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao limparo texto do elemento: " + this.toString() + ". Erro: " + e, true, device);
		}
		TestBaseMobile.logReport(Status.INFO, "Limpeza de texto do elemento: " + this.toString(), false, device);
		return this;
	}
	
	/**
	 * Aguarda o elemento existir
	 * 
	 * @param tempoEsperaSegundos
	 * @return ElementoMobile
	 */
	public ElementoMobile aguardarElementoExistir(int tempoEsperaSegundos) {
		
		
		try {
			
			if (verificarElementoExiste(tempoEsperaSegundos)) {
				TestBaseMobile.logReport(Status.INFO, "Aguardado elemento existir. Timeout: "
						+ tempoEsperaSegundos + " segundos. Locator: " + elementoLocator.toString(), false, device);
			}
			else {
				TestBaseMobile.logReport(Status.FAIL,
						"Erro! Elemento: " + this.toString() + " não apareceu após aguardar " + tempoEsperaSegundos + " segundos." , true, device);
			}
			
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao aguardar elemento existir: " + this.toString() + ". Erro: " + e, true, device);
		}
		return localizarElemento();
	}
	
	/**
	 * Aguarda o elemento ficar visivel
	 * 
	 * @param tempoEsperaSegundos
	 * @return ElementoMobile
	 */
	public ElementoMobile aguardarElementoFicarVisivel(int tempoEsperaSegundos) {
		
		WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
		try {

				wait.until(ExpectedConditions.visibilityOfElementLocated(elementoLocator));
				TestBaseMobile.logReport(Status.INFO, "Aguardado elemento ficar visivel. Timeout: "
						+ tempoEsperaSegundos + " segundos. Locator: " + elementoLocator.toString(), false, device);
			
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			wait.until(ExpectedConditions.visibilityOfElementLocated(elementoLocator));
			TestBaseMobile.logReport(Status.INFO, "Aguardado elemento ficar visivel. Timeout: " + tempoEsperaSegundos
					+ " segundos. Locator: " + elementoLocator.toString(), false, device);
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao aguardar visibilidade do elemento: " + this.toString() + ". Erro: " + e, true, device);
		}
		return localizarElemento();
	}

	/**
	 * Aguarda o elemento ficar invisível
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return ElementoMobile
	 */
	public ElementoMobile aguardarElementoFicarInvisivel(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.invisibilityOfElementLocated(elementoLocator));
			TestBaseMobile.logReport(Status.INFO, "Aguardado elemento ficar invisvel. Timeout: " + tempoEsperaSegundos
					+ " segundos. Elemento: " + elementoLocator.toString(), false, device);
		} catch (NullPointerException e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao aguardar elemento: " + this.toString() + " ficar invisível. Erro: " + e, true, device);
		}
		return localizarElemento();
	}
	
	/**
	 * Aguarda o elemento nao existir mais
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return ElementoMobile
	 */
	public ElementoMobile aguardarElementoSairDaTela(int tempoEsperaSegundos) {
		try {
			for (int cont = 0; cont < tempoEsperaSegundos; cont++) {
				if (verificarElementoExiste()) {
					Thread.sleep(1000);
				}else {
					TestBaseMobile.logReport(Status.INFO, "Aguardado elemento sair da tela. Timeout: " + tempoEsperaSegundos
							+ " segundos. Elemento: " + elementoLocator.toString(), false, device);
					return this;
				}
			}
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao aguardar elemento: " + this.toString() + " sair da tela. Erro: " + e, true, device);
		}
		TestBaseMobile.logReport(Status.FAIL, "Erro. Elemento "+elementoLocator.toString()+" não saiu da tela após tempo limite de espera. Timeout: " + tempoEsperaSegundos
				+ " segundos. Elemento: " + elementoLocator.toString(), false, device);
		return this;
	}

	/**
	 * Aguarda o elemento ficar clicável
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return ElementoMobile
	 */
	public ElementoMobile aguardarElementoFicarClicavel(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.elementToBeClickable(elementoLocator));
			TestBaseMobile.logReport(Status.INFO, "Aguardado elemento ficar clicável. Timeout: " + tempoEsperaSegundos
					+ " segundos. Elemento: " + elementoLocator.toString(), false, device);
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao aguardar elemento: " + this.toString() + " ficar clicável. Erro: " + e, true, device);
		}
		return localizarElemento();
	}

	/**
	 * Verifica se elemento fica visível apos aguardar o tempo de espera
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return Boolean True - Elemento encontrado / False - Elemento nao encontrado
	 */
	public Boolean verificaElementoFicaVisivelAposEspera(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.visibilityOfElementLocated(elementoLocator));
			localizarElemento();
			return true;
		} catch (Exception e) {
			return false;
		}
	}
	

	/**
	 * Verifica a visibilidade do elemento (isDisplayed)
	 * 
	 * @return Boolean
	 */
	public Boolean verificaVisibilidade() {
		if (elemento == null)
			localizarElemento();
		Boolean elementoVisivel = null;
		try {
			elementoVisivel = elemento.isDisplayed();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elementoVisivel = elemento.isDisplayed();
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao verificar visibilidade do elemento: " + this.toString() + ". Erro: " + e, true, device);
		}
		return elementoVisivel;
	}

	/**
	 * Verifica se o elemento esta habilitado (isEnabled)
	 * 
	 * @return Boolean
	 */
	public Boolean verificaHabilitado() {
		if (elemento == null)
			localizarElemento();
		Boolean elementoDisponivel = null;
		try {
			elementoDisponivel = elemento.isEnabled();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elementoDisponivel = elemento.isEnabled();
		} catch (Exception e) {
			TestBaseMobile.logReport(Status.FAIL,
					"Erro ao verificar se elemento: " + this.toString() + " esta habilitado. Erro: " + e, true, device);
		}
		return elementoDisponivel;
	}

	/**
	 * Reseta o elemento, caso seja necessário interagir com o mesmo elemento novamente
	 */
	public void resetarElemento() {
		elemento = null;
	}
	
	/**
	 * Montar o locator do elemento
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para pesquisa
	 * @return By Locator do elemento web
	 */
	protected static By montarLocator(AtributoMobile atributo, String valor) {
		By by = null;
		switch (atributo) {
		case Id:
			by = By.id(valor);
			break;
		case Name:
			by = By.name(valor);
			break;
		case ClassName:
			by = By.className(valor);
			break;
		case CssSelector:
			by = By.cssSelector(valor);
			break;
		case LinkText:
			by = By.linkText(valor);
			break;
		case PartialLinkText:
			by = By.partialLinkText(valor);
			break;
		case TagName:
			by = By.tagName(valor);
			break;
		case Xpath:
			by = By.xpath(valor);
			break;
		case Predicate:
			by = MobileBy.iOSNsPredicateString(valor);
			break;
		case AccessibilityId:
			by = MobileBy.AccessibilityId(valor);
			break;
		}
		return by;
	}
}
