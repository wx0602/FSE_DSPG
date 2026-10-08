package grupopanqa.automacao.web.elementos;

import grupopanqa.automacao.util.EnumFramework.AtributoWeb;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.web.Navegador;
import grupopanqa.automacao.web.TestBaseWeb;
import org.openqa.selenium.StaleElementReferenceException;

/**
 * Classe com metodos do elemento CheckBox encapsulado
 * 
 * @author 800041563
 *
 */
public class CheckBox extends ElementoWeb {

	/**
	 * Construtor - envia os atributos para ElementoWeb
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param driver
	 */
	public CheckBox(AtributoWeb atributo, String valor, Navegador navegador) {
		super(atributo, valor, navegador);
	}

	/**
	 * Construtor utilizado quando o elemento e instanciado pelo ElementosWeb (lista
	 * de elementos)
	 * 
	 * @param elementosWeb Lista de elementos web
	 * @param index        Posicao do elemento da lista a possuir iteracao
	 */
	public CheckBox(ElementosWeb elementosWeb, int index) {
		super(elementosWeb, index);
	}

	/**
	 * Realiza o check no elemento caso não esteja marcado (para checkbox,
	 * radiobutton e combobox)
	 * 
	 * @return ElementoWeb
	 */
	public CheckBox marcar() {
		if (elemento == null)
			localizarElemento();
		Boolean marcado = null;
		try {
			marcado = elemento.isSelected();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			marcado = elemento.isSelected();
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao tentar realizar a marcacao do elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}
		if (!marcado) {
			elemento.click();
		}
		TestBaseWeb.logReport(Status.INFO, "Realizado/Validado marcacao do elemento: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Realiza a remocao do check no elemento caso esteja marcado (para checkbox,
	 * radiobutton e combobox)
	 * 
	 * @return ElementoWeb
	 */
	public CheckBox desmarcar() {
		if (elemento == null)
			localizarElemento();
		Boolean marcado = null;
		try {
			marcado = elemento.isSelected();
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			marcado = elemento.isSelected();
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao tentar realizar a desmarcacao do elemento: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}

		if (marcado) {
			elemento.click();
		}
		TestBaseWeb.logReport(Status.INFO, "Realizado/Validado desmarcacao do elemento: " + elemento.toString(), false, navegador);
		return this;
	}
}
