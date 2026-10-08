package grupopanqa.automacao.web.elementos;

import grupopanqa.automacao.util.EnumFramework.AtributoWeb;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.web.Navegador;
import grupopanqa.automacao.web.TestBaseWeb;
import org.openqa.selenium.StaleElementReferenceException;
import org.openqa.selenium.support.ui.Select;

import java.util.Random;

/**
 * Classe com metodos do elemento ComboBox encapsulado
 * 
 * @author 800041563
 *
 */
public class ComboBox extends ElementoWeb{

	/**
	 * Construtor - envia os atributos para ElementoWeb
	 * 
	 * @param atributo Atributo do elemento (ex: Id, Name, ClasseName...)
	 * @param valor    Valor do atributo para localizar o elemento
	 * @param driver
	 */
	public ComboBox(AtributoWeb atributo, String valor, Navegador navegador) {
		super(atributo, valor, navegador);

	}

	/**
	 * Construtor utilizado quando o elemento e instanciado pelo ElementosWeb (lista de elementos)
	 * @param elementosWeb Lista de elementos web
	 * @param index Posicao do elemento da lista a possuir iteracao
	 */
	public ComboBox(ElementosWeb elementosWeb, int index) {
		super(elementosWeb, index);
	}

	/**
	 * Seleciona item do combobox pelo texto visivel
	 * 
	 * @param opcao String com o texto a ser selecionado
	 * @return ElementoWeb
	 */
	public ComboBox selecionarPeloTexto(String opcao) {
		if (elemento == null)
			localizarElemento();
		try {
			new Select(elemento).selectByVisibleText(opcao);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			new Select(elemento).selectByVisibleText(opcao);
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao tentar selecionar no combobox: " + elemento.toString() + " o texto: "+ opcao +". Erro: " + e, true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Selecionado texto: " +opcao + " do ComboBox: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Seleciona item do combobox pelo value
	 * 
	 * @param opcao String com o valor a ser selecionado
	 * @return ElementoWeb
	 */
	public ComboBox selecionarPeloValor(String opcao) {
		if (elemento == null)
			localizarElemento();
		try {
			new Select(elemento).selectByValue(opcao);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			new Select(elemento).selectByValue(opcao);
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao tentar selecionar no combobox: " + elemento.toString() + " o valor: "+ opcao +". Erro: " + e, true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Selecionado valor: " +opcao + " do ComboBox: " + elemento.toString(), false, navegador);
		return this;
	}
	
	/**
	 * Seleciona item do combobox pelo index
	 * 
	 * @param index int com o index a ser selecionado
	 * @return ElementoWeb
	 */
	public ComboBox selecionarPeloIndex(int index) {
		if (elemento == null)
			localizarElemento();
		try {
			new Select(elemento).selectByIndex(index);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			new Select(elemento).selectByIndex(index);
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao tentar selecionar no combobox: " + elemento.toString() + " o index: "+ index +". Erro: " + e, true, navegador);
		}
		TestBaseWeb.logReport(Status.INFO, "Selecionado index: " +index + " do ComboBox: " + elemento.toString(), false, navegador);
		return this;
	}

	/**
	 * Seleciona item do combobox de forma aleatoria
	 * 
	 * @param indexInicial Informa a partir de qual index deve ser levado em
	 *considecarao. Valor 0 sera levado em consideracao todas as opcoes
	 * @return ElementoWeb
	 */
	public ComboBox selecionarOpcaoAleatorio(int indexInicial) {
		if (elemento == null)
			localizarElemento();
		Select elementoSelect = null;
		try {
			elementoSelect = new Select(elemento);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elementoSelect = new Select(elemento);
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao tentar selecionar no combobox: " + elemento.toString() + " um valor aleatorio. Erro: " + e, true, navegador);
		}
		int qtdItensSelect = elementoSelect.getOptions().size();
		Random gerador = new Random();
		int numeroAleatorio = gerador.nextInt(qtdItensSelect - indexInicial);
		elementoSelect.selectByIndex(numeroAleatorio);
		TestBaseWeb.logReport(Status.INFO, "Selecionado aleatoriamente index " + numeroAleatorio + " do ComboBox: " + elemento.toString(), false, navegador);
		return this;
	}
	/**
	 * Recuperar quantidade de opcoes do combo box
	 * 
	 * @return int Quantidade de opcoes
	 */
	public int recuperarQuantidadeOpcoes() {
		if (elemento == null)
			localizarElemento();
		Select elementoSelect = null;
		try {
			elementoSelect = new Select(elemento);
		} catch (StaleElementReferenceException e) {
			localizarElemento();
			elementoSelect = new Select(elemento);
		}
		catch (Exception e) {
			TestBaseWeb.logReport(Status.FAIL, "Erro ao recuperar quantidade de itens do combobox: " + elemento.toString() + ". Erro: " + e, true, navegador);
		}
		int qtdItensSelect = elementoSelect.getOptions().size();
		return qtdItensSelect;
	}
}
