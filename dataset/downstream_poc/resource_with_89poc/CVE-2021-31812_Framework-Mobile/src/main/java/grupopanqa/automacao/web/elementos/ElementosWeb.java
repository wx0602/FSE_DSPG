package grupopanqa.automacao.web.elementos;

import grupopanqa.automacao.util.EnumFramework.AtributoWeb;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/**
 * Classe com metodos referente a lista de elementosWeb
 * 
 * @author 800041563
 *
 */
public class ElementosWeb {

	private WebDriver driver;
	private By elementoLocator;
	private AtributoWeb atributoElemento;
	private String valorElemento;

	/**
	 * Objeto para iteracao com os elementos web
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param driver
	 */
	public ElementosWeb(AtributoWeb atributo, String valor, WebDriver driver) {
		this.driver = driver;
		atributoElemento = atributo;
		valorElemento = valor;
		elementoLocator = ElementoWeb.montarLocator(atributo, valor);
	}

	public WebDriver getDriver() {
		return driver;
	}

	public AtributoWeb getAtributoElemento() {
		return atributoElemento;
	}

	public String getValorElemento() {
		return valorElemento;
	}

	/**
	 * Atualiza o valor da elemento (atributo) de acordo com o informado por
	 * parametro
	 * 
	 * @param valorAntigo String a ser removida
	 * @param valorNovo   String nova a ser inserida no lugar
	 */
	public void atualizarValorLocator(String valorAntigo, String valorNovo) {
		valorElemento = valorElemento.replace(valorAntigo, valorNovo);
		elementoLocator = ElementoWeb.montarLocator(atributoElemento, valorElemento);
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
	 * Metodo para recuperar um dos elementos da lista de elementosWeb de acordo com
	 * o Index
	 * 
	 * @param index Int com o valor a ser recuperado (inicia com 0)
	 * @return ElementoWeb com o elemento encontrado
	 */
	public ElementoWeb recuperarElementoPorIndex(int index) {
		ElementoWeb elementoSelecionado = new ElementoWeb(this, index);
		return elementoSelecionado;
	}

	/**
	 * Metodo para recuperar um dos elementos da lista de CheckBox de acordo com o
	 * Index
	 * 
	 * @param index Int com o valor a ser recuperado (inicia com 0)
	 * @return CheckBox com o elemento encontrado
	 */
	public CheckBox recuperarCheckBoxPorIndex(int index) {
		CheckBox elementoSelecionado = new CheckBox(this, index);
		return elementoSelecionado;
	}

	/**
	 * Metodo para recuperar um dos elementos da lista de ComboBox de acordo com o
	 * Index
	 * 
	 * @param index Int com o valor a ser recuperado (inicia com 0)
	 * @return ComboBox com o elemento encontrado
	 */
	public ComboBox recuperarComboBoxPorIndex(int index) {
		ComboBox elementoSelecionado = new ComboBox(this, index);
		return elementoSelecionado;
	}
}
