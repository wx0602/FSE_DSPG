package grupopanqa.automacao.web.elementos;

import grupopanqa.automacao.util.EnumFramework.AtributoWeb;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.web.Navegador;
import grupopanqa.automacao.web.TestBaseWeb;
import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

/**
 * Classe com metodos do elemento web
 * 
 * @author 800041563
 *
 */
public class ElementoWeb {

	protected WebElement elemento;

	private WebDriver driver;
	private By elementoLocator;
	private Actions action;
	private AtributoWeb atributoElemento;
	private String valorElemento;
	protected Navegador navegador;

	// quando o indexElemento é diferente de -1, quer dizer que o elemento se trata
	// de uma lista de elementos e o index a posicao
	// a ser utilizada
	private int indexElemento = -1;

	/**
	 * Iteracao com o elemento web
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param driver
	 */
	public ElementoWeb(AtributoWeb atributo, String valor, Navegador navegador) {
		this.navegador = navegador;
		this.driver = navegador.getDriver();
		atributoElemento = atributo;
		valorElemento = valor;
		elementoLocator = montarLocator(atributo, valor);
	}

	/**
	 * Construtor utilizado quando o elemento e instanciado pelo ElementosWeb (lista
	 * de elementos)
	 * 
	 * @param elementosWeb Lista de elementos web
	 * @param index        Posicao do elemento da lista a possuir iteracao
	 */
	public ElementoWeb(ElementosWeb elementosWeb, int index) {
		driver = elementosWeb.getDriver();
		indexElemento = index;
		valorElemento = elementosWeb.getValorElemento();
		atributoElemento = elementosWeb.getAtributoElemento();
		elementoLocator = montarLocator(atributoElemento, valorElemento);
	}

	/**
	 * Objeto para iteracao com os elementos web
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param driver
	 */
	public void atualizarValorLocator(String valorAntigo, String valorNovo) {
		valorElemento = valorElemento.replace(valorAntigo, valorNovo);
		elementoLocator = montarLocator(atributoElemento, valorElemento);
	}

	/**
	 * Metodo para buscar o elemento web na pagina
	 * 
	 * @return ElementoWeb Retorna o elemento web
	 */
	public ElementoWeb localizarElemento() {
		if (verificarElementoExiste()) {
			// Verifica se o elemento a ser utilizado e unico ou veio de uma lista - nesse
			// caso e utilizado o index
			if (indexElemento == -1) {
				elemento = driver.findElement(elementoLocator);
			} else {
				elemento = driver.findElements(elementoLocator).get(indexElemento);
			}
		} else {
			elemento = null;
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
	 * Metodo para verificar se existe o elemento web na pagina
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
	 * Metodo para verificar se existe o elemento web na pagina com timeout
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
	 * @return ElementoWeb
	 */
	public ElementoWeb clicar() {
		if (elemento == null)
			localizarElemento();
		try {
			elemento.click();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.click();
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao clicar no elemento: " + elemento.toString() + ". Erro: " + e,
					true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Realizado click no elemento: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Recupera o texto do elemento web
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
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao recuperar texto do elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}
		return texto;
	}

	/**
	 * Recupera o atributo do elemento web
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
			TestBaseWeb.logReport(Status.FAIL, "Erro ao recuperar atributo '" + atributo + "' do elemento: "
					+ elemento.toString() + ". Erro: " + e, true, navegador);
		}

		return valorAtributo;
	}

	/**
	 * Realiza a digitacao de texto no elemento web
	 * 
	 * @param texto String a ser digitado
	 * @return ElementoWeb
	 */
	public ElementoWeb digitar(String texto) {
		if (elemento == null)
			localizarElemento();

		try {
			elemento.sendKeys(texto);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.sendKeys(texto);
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao digitar o texto '" + texto + "' no elemento: " + elemento.toString() + ". Erro: " + e,
					true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Digitado texto: " + texto + " no elemento: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Realiza a digitacao no elemento com TAB
	 * 
	 * @param texto String a ser digitado
	 * @return ElementoWeb
	 */
	public ElementoWeb digitarComTab(String texto) {
		if (elemento == null)
			localizarElemento();
		elemento.toString();
		try {
			elemento.sendKeys(texto + Keys.TAB);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.sendKeys(texto + Keys.TAB);
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao digitar (com tab) o texto '" + texto + "' no elemento: "
					+ elemento.toString() + ". Erro: " + e, true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Digitado texto: " + texto + " + TAB no elemento: " + elemento.toString(),
				false, navegador);
		return this;
	}

	/**
	 * Colocar focus no elemento
	 * 
	 * @return ElementoWeb
	 */
	public ElementoWeb focus() {
		elemento.sendKeys(Keys.SHIFT);
		JavascriptExecutor jse = (JavascriptExecutor) driver;
		jse.executeScript("elemento.focus();");
		TestBaseWeb.logReport(Status.INFO, "Focus no elemento: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Realiza a limpeza do elemento (retira texto do elemento caso possua)
	 * 
	 * @return ElementoWeb
	 */
	public ElementoWeb limparTexto() {
		if (elemento == null)
			localizarElemento();

		try {
			elemento.clear();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elemento.clear();
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao limparo texto do elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Limpeza de texto do elemento: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Aguarda o elemento ficar visivel
	 * 
	 * @param tempoEsperaSegundos
	 * @return ElementoWeb
	 */
	public ElementoWeb aguardarElementoFicarVisivel(int tempoEsperaSegundos) {
		WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
		try {
			if (elemento == null) {
				wait.until(ExpectedConditions.visibilityOfElementLocated(elementoLocator));
				TestBaseWeb.logReport(Status.INFO, "Aguardado elemento ficar visivel. Timeout: " + tempoEsperaSegundos
						+ " segundos. Locator: " + elementoLocator.toString(), false, navegador);
			} else {
				wait.until(ExpectedConditions.visibilityOf(elemento));
				TestBaseWeb.logReport(Status.INFO, "Aguardado elemento ficar visivel. Timeout: " + tempoEsperaSegundos
						+ " segundos. Elemento: " + elemento.toString(), false, navegador);
			}
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			wait.until(ExpectedConditions.visibilityOfElementLocated(elementoLocator));
			TestBaseWeb.logReport(Status.INFO, "Aguardado elemento ficar visivel. Timeout: " + tempoEsperaSegundos
					+ " segundos. Locator: " + elementoLocator.toString(), false, navegador);
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao aguardar visibilidade do elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}
		return localizarElemento();
	}

	/**
	 * Aguarda o elemento ficar invisivel
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return ElementoWeb
	 */
	public ElementoWeb aguardarElementoFicarInvisivel(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.invisibilityOfElementLocated(elementoLocator));
			TestBaseWeb.logReport(Status.INFO, "Aguardado elemento ficar invisivel. Timeout: " + tempoEsperaSegundos
					+ " segundos. Elemento: " + elementoLocator.toString(), false, navegador);
		} catch (NullPointerException e) {
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao aguardar elemento: " + elemento.toString() + " ficar invisivel. Erro: " + e, true, navegador);
		}
		return localizarElemento();
	}

	/**
	 * Aguarda o elemento ficar clicavel
	 * 
	 * @param tempoEsperaSegundos Quantidade de segundos para aguardar
	 * @return ElementoWeb
	 */
	public ElementoWeb aguardarElementoFicarClicavel(int tempoEsperaSegundos) {
		try {
			WebDriverWait wait = new WebDriverWait(driver, tempoEsperaSegundos);
			wait.until(ExpectedConditions.elementToBeClickable(elementoLocator));
			TestBaseWeb.logReport(Status.INFO, "Aguardado elemento ficar clicavel. Timeout: " + tempoEsperaSegundos
					+ " segundos. Elemento: " + elementoLocator.toString(), false, navegador);
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao aguardar elemento: " + elemento.toString() + " ficar clicavel. Erro: " + e, true, navegador);
		}
		return localizarElemento();
	}

	/**
	 * Verifica se elemento fica visivel apos aguardar o tempo de espera
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
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao verificar visibilidade do elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
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
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao verificar se elemento: " + elemento.toString() + " esta habilitado. Erro: " + e, true, navegador);
		}
		return elementoDisponivel;
	}

	/**
	 * Montar o locator do elemento
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para pesquisa
	 * @return By Locator do elemento web
	 */
	protected static By montarLocator(AtributoWeb atributo, String valor) {
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
		}
		return by;
	}

	/**
	 * Movimenta o mouse até o elemento web
	 * 
	 * @param esperaSegundos Quantidade de segundo para manter o mouse em cima do
	 *                       elemento
	 */
	public void moverMouseAteElemento(int esperaSegundos) {
		try {
			if (elemento == null)
				localizarElemento();
			if (action == null)
				action = new Actions(driver);
			try {
				action.moveToElement(elemento);
				action.perform();
			} catch (StaleElementReferenceException e) {
				localizarElemento();
				action.moveToElement(elemento);
				action.perform();
			}

			Thread.sleep(esperaSegundos * 1000);
			TestBaseWeb.logReport(Status.INFO, "Mouse movido ate o elemento: " + elemento.toString(), false, navegador);
		} catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL,
					"Erro ao mover ou mouse ate o elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}
	}
}
