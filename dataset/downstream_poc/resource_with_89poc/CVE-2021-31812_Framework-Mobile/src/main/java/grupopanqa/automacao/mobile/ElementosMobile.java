package grupopanqa.automacao.mobile;

import grupopanqa.automacao.util.EnumFramework.AtributoMobile;
import io.appium.java_client.AppiumDriver;
import org.openqa.selenium.By;

/**
 * Classe com metodos referente a lista de elementos mobile
 * 
 * @author 800041563
 *
 */
public class ElementosMobile {

	private AppiumDriver<?> driver;
	private By elementoLocator;
	private AtributoMobile atributoElemento;
	private String valorElemento;
	/**
	 * Construtor da lista de elementos mobile
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param device Instância do device
	 */
	public ElementosMobile(AtributoMobile atributo, String valor, Device device) {
		this.driver = device.getDriver();
		atributoElemento = atributo;
		valorElemento = valor;
		elementoLocator = ElementoMobile.montarLocator(atributo, valor);
	}

	public AppiumDriver<?> getDriver() {
		return driver;
	}

	public AtributoMobile getAtributoElemento() {
		return atributoElemento;
	}

	public String getValorElemento() {
		return valorElemento;
	}

	/**
	 * Atualiza o valor da elemento (atributo) de acordo com o informado por
	 * parâmetro
	 * 
	 * @param valorAntigo String a ser removida
	 * @param valorNovo   String nova a ser inserida no lugar
	 */
	public void atualizarValorLocator(String valorAntigo, String valorNovo) {
		valorElemento = valorElemento.replace(valorAntigo, valorNovo);
		elementoLocator = ElementoMobile.montarLocator(atributoElemento, valorElemento);
	}

	/**
	 * Método para retornar quantidades de elementos encontrados no device
	 * 
	 * @return int quantidade de elementos
	 */
	public int contadorElementos() {
		int contador = driver.findElements(elementoLocator).size();
		return contador;
	}

	/**
	 * Método para recuperar um dos elementos da lista de elementos mobile de acordo com
	 * o Index
	 * 
	 * @param index Int com o valor a ser recuperado (inicia com 0)
	 * @return ElementoWeb com o elemento encontrado
	 */
	public ElementoMobile recuperarElementoPorIndex(int index) {
		ElementoMobile elementoSelecionado = new ElementoMobile(this, index);
		return elementoSelecionado;
	}

}
