package grupopanqa.automacao.mobile;

import static grupopanqa.automacao.mobile.ConfigMobile.ifAndroid;
import static grupopanqa.automacao.mobile.TestBaseMobile.logReport;
import static io.appium.java_client.touch.WaitOptions.waitOptions;
import static io.appium.java_client.touch.offset.PointOption.point;
import static java.time.Duration.ofMillis;
import static java.util.Arrays.asList;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import org.openqa.selenium.Dimension;
import org.openqa.selenium.Point;

import grupopanqa.automacao.util.EnumFramework.Direcao;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.EnumFramework.Velocidade;
import io.appium.java_client.AppiumDriver;
import io.appium.java_client.MobileElement;
import io.appium.java_client.TouchAction;
import io.appium.java_client.touch.WaitOptions;
import io.appium.java_client.touch.offset.PointOption;

/**
 * Classe responsavel por extender todas as classes de PageObject
 * 
 * @author 800041563
 *
 */
public class PageObject {

	protected int posicaoVertical = 0;
	protected Boolean located = false;
	protected AppiumDriver<?> driver;
	protected Device device;
	@SuppressWarnings("rawtypes")
	protected static TouchAction actions;
	
	/**
	 * Realiza a inicializacao dos elementos do pageobject
	 * 
	 * @param navegador
	 */
	@SuppressWarnings("rawtypes")
	public PageObject(Device device) {
		this.device = device;
		this.driver = device.getDriver();
		actions = new TouchAction(this.driver);
		
		ifAndroid(this::android, this::ios);
	}
	
	public void android() { }
	
	public void ios() { }

	/**
	 * Esconde o teclado do device
	 */
	public void esconderTeclado() {
		driver.hideKeyboard();
	}
	
	/**
	 * Realiza o gesto de clicar de um ponto ao outro
	 * @param elemento Elemento principal para ação
	 * @param percentual percentual que será realizado tap
	 */
	public void tapSliderLeft(ElementoMobile elemento, double percentualTela) {
		Dimension size = driver.manage().window().getSize();
		System.out.println(size.toString());
		int delta = 50;
		
		int y = elemento.getMobileElement().getLocation().y + (elemento.getMobileElement().getSize().height / 2);
		System.out.println(y);
		
		int xinicial = elemento.getMobileElement().getLocation().x + delta;
		int x = (int) (xinicial + ((elemento.getMobileElement().getSize().width - 2 * delta) * percentualTela));
		System.out.println(x);
		
		actions.tap(PointOption.point(x, y)).perform();
	}
	
	/**
	 * Realiza a comparação entre uma String e o texto de um elemento
	 * @param String que será comparada
	 * @param texto obtido de um elemento
	 */
	public void validarTextoContemDado(String texto, String dadoBuscado) {
		if (texto.contains(dadoBuscado)) {
			TestBaseMobile.logReport(Status.PASS,
					"Validado que o texto: '" + texto + "' possui a seguinte informação: '" + dadoBuscado + "'", false,
					device);
		} else {
			TestBaseMobile.logReport(Status.FAIL, "Falha! Não foi possível encontrar no texto: '" + texto + "' a seguinte informação: '" + dadoBuscado + "'", true, device);
		}
	}
	
	/**
	 * Verifica se o Elemento está na tela de acordo com o timeout
	 * @param ' principal para ação
	 * @param quantidade de vezes que deverá procurar o elemento
	 */
	public boolean waitExist(ElementoMobile obj, Integer timeout) {
		Boolean element = null;
		located = false;
		for (int i = 1; i <= timeout; i++) {
			element = obj.verificarElementoExiste(1);
			if (element != false) {
				located = true;
				System.out.println("Element '" + obj + "' located");
				break;
			} else
				try {
					System.out.println("Cannot find the Element '" + obj + "' times " + i + " of " + timeout);
					Thread.sleep(1000);
				} catch (InterruptedException e) {
					;
				}
		}
		return located;
	}
	
	/**
	 * Verifica se o Elemento está na tela de acordo com o timeout e realiza ação de click
	 * @param ' principal para ação
	 * @param quantidade de vezes que deverá procurar o elemento
	 */
	public boolean waitExistClick(ElementoMobile elemento, Integer timeout) {
		ElementoMobile element = null;
		located = false;
		for (int i = 1; i <= timeout; i++) {
			element = elemento.localizarElemento();
			if (element != null) {
				located = true;
				System.out.println("Element '" + elemento + "' located");
				elemento.clicar();
				break;
			} else
				try {
					System.out.println("Cannot find the Element '" + elemento + "' times " + i + " of " + timeout);
					Thread.sleep(1000);
				} catch (InterruptedException e) {
					;
				}
		}
		return located;
	}
	
	/**
	 * Realiza o gesto de deslizar até o elemento
	 * @param Elemento principal para ação
	 * @param percentual da tela que será realizado a ação
	 */
	public void swipeUntilElementLeft(ElementoMobile obj, double percentualTela) {

		Dimension size = driver.manage().window().getSize();
		System.out.println(size.toString());

		int y = (int) (size.height * percentualTela);
		int start_x = (int) (size.width * 0.9);
		int end_x = (int) (size.width * 0.1);
		int i = 0;

		System.out.println(y + " - " + start_x + " - " + end_x);

		Boolean objFinded = obj.verificarElementoExiste(1);
		if (!objFinded == true) {
			while (objFinded == false) {
				actions.press(PointOption.point(start_x, y));
				actions.waitAction(WaitOptions.waitOptions(ofMillis(1000)));
				actions.moveTo(PointOption.point(end_x, y)).release().perform();
				objFinded = obj.verificarElementoExiste(1);
				i++;
				if (i == 13)
					break;
			}
		} else
			System.out.println("Objeto nao localizado na tela " + obj);
	}
	
	/**
	 * Realiza o gesto de deslizar até o elemento
	 * @param Elemento principal para ação
	 * @param percentual da tela que será realizado a ação
	 */
	public void swipeUntilElementRight(ElementoMobile obj, double percentualTela) {

		Dimension size = driver.manage().window().getSize();
		System.out.println(size.toString());

		int y = (int) (size.height * percentualTela);
		int start_x = (int) (size.width * 0.1);
		int end_x = (int) (size.width * 0.9);
		int i = 0;

		System.out.println(y + " - " + start_x + " - " + end_x);

		Boolean objFinded = obj.verificarElementoExiste(1);
		if (!objFinded == true) {
			while (objFinded == false) {
				actions.press(PointOption.point(start_x, y));
				actions.waitAction(WaitOptions.waitOptions(ofMillis(1000)));
				actions.moveTo(PointOption.point(end_x, y)).release().perform();
				objFinded = obj.verificarElementoExiste(1);
				i++;
				if (i == 13)
					break;
			}
		} else
			System.out.println("Objeto nao localizado na tela " + obj);
	}
	
	
	/**
	 * Realiza o gesto de deslizar de um elemento para outro
	 * @param inicio Elemento inicial que será arrastado
	 * @param fim Elemento final que será o ponto final do elemento inicial
	 */
	public void deslizarElementoAteOutroElemento(ElementoMobile inicio, ElementoMobile fim) {
		deslizarElementoAteOutroElemento(inicio, fim, Velocidade.NORMAL);
	}
	
	/**
	 * Realiza o gesto de deslizar de um elemento para outro
	 * @param inicio Elemento inicial que será arrastado
	 * @param fim Elemento final que será o ponto final do elemento inicial
	 */
	public void deslizarElementoAteOutroElemento(ElementoMobile inicio, ElementoMobile fim, Velocidade velocidade) {
		Point coordElementoInicial = inicio.getMobileElement().getLocation();
		Point coordElementoFinal = fim.getMobileElement().getLocation();
		PointOption<?> pointOptionInicial = PointOption.point(coordElementoInicial.getX(), coordElementoInicial.getY());
		PointOption<?> pointOptionFinal = PointOption.point(coordElementoFinal.getX(), coordElementoFinal.getY());
		deslizarDePara(pointOptionInicial, pointOptionFinal, velocidade);
	}
	
	/**
	 * Realiza o gesto de deslizar no device
	 * @param direcao Direção para onde será realizado o gesto
	 */
	public void deslizarTela(Direcao direcao) {
		deslizarTela(direcao, Velocidade.NORMAL);
	}
	
	public void swipeUntilElementAndValidate(ElementoMobile containerToSwipe, Direcao direcao, ElementoMobile elementToFind) {
		swipeUntilElementAndValidate(containerToSwipe, direcao, elementToFind, true);
	}
	
	public void swipeUntilElementAndValidate(ElementoMobile containerToSwipe, Direcao direcao, ElementoMobile elementToFind, boolean validateVisible) {
		if (!swipeUntilElement(containerToSwipe, direcao, elementToFind, validateVisible)) {
			logReport(Status.FAIL, "Erro ao aguardar elemento existir: " + elementToFind.toString(), true, device);
		}
	}
	
	public boolean swipeUntilElement(ElementoMobile containerToSwipe, Direcao direcao, ElementoMobile elementToFind) {
		return swipeUntilElement(containerToSwipe, direcao, elementToFind, true);
	}
	
	/**
	 * Baseado na posição e tamanho do container informado, é realizado movimento de swipe dentro deste container até encontrar o elemento desejado
	 * @param containerToSwipe
	 * @param direcao
	 * @param elementToFind
	 */
	public boolean swipeUntilElement(ElementoMobile containerToSwipe, Direcao direcao, ElementoMobile elementToFind, boolean validateVisible) {
		containerToSwipe.aguardarElementoExistir(20);
		MobileElement containerMobileElement = containerToSwipe.getMobileElement();

		int i = 0;
		
		while(true) {
			elementToFind.resetarElemento();
			
			boolean objFinded = elementToFind.verificarElementoExiste(3);
			
			if (objFinded && (!validateVisible || elementToFind.verificaVisibilidade())) return true;
			
			if (i > 12) return false; // Para o futuro verificar como interromper ao chegar no fim do container
			
			i++;
			
			deslizarTela(direcao, Velocidade.NORMAL, containerMobileElement);
		}
	}
	
	public static ElementoMobile obterPrimeiroVisivel(Integer timeoutSeconds, ElementoMobile... el) {
		Long start = System.currentTimeMillis();
		List<ElementoMobile> elements = asList(el);

		Long timeoutMilisseconds = (long) (timeoutSeconds * 1000);

		do {
			Optional<ElementoMobile> elemento = elements.stream()
					.filter(it -> it.verificarElementoExiste() && it.verificaVisibilidade()).findFirst();
			if (elemento.isPresent())
				return elemento.get();

			aguardarSeguro(500L);
		} while (System.currentTimeMillis() - start < timeoutMilisseconds);

		return null;
	}
	
	public static void aguardarSeguro(Long time) {
		try {
			Thread.sleep(time);
		} catch (InterruptedException e) {
			Thread.currentThread().interrupt();
			e.printStackTrace();
		}
	}

	/**
	 * Realiza o gesto de deslizar no device
	 * @param direcao Direção para onde será realizado o gesto
	 * @param velocidade
	 */
	public void deslizarTela(Direcao direcao, Velocidade velocidade) {
		PointOption<?> pontoInicial = null;
		PointOption<?> pontoFinal = null;
		switch(direcao) {
		case PARA_CIMA:
			pontoInicial = PointOption.point(0, alturaTela());
			pontoFinal = PointOption.point(0, 0);
			break;
		case PARA_BAIXO:
			pontoInicial = PointOption.point(0, 100);
			pontoFinal = PointOption.point(0, alturaTela());
			break;
		case PARA_DIREITA:
			pontoInicial = PointOption.point(0, alturaTela()/2);
			pontoFinal = PointOption.point(larguraTela(), alturaTela()/2);
			break;
		case PARA_ESQUERDA:
			pontoInicial = PointOption.point(larguraTela(), alturaTela()/2);
			pontoFinal = PointOption.point(0, alturaTela()/2);
			break;
		}
		deslizarDePara(pontoInicial, pontoFinal, velocidade);
	}
	
	public void deslizarTela(Direcao direcao, Velocidade velocidade, MobileElement container) {
		PointOption<?> pontoInicial = null;
		PointOption<?> pontoFinal = null;
		
		Point location = container.getLocation();
		Dimension size = container.getSize();
		Dimension windowSize = driver.manage().window().getSize();
		
		int posicaoMetadeX = (size.width / 2) + location.x;
		int posicaoMetadeY = (size.height / 2) + location.y;
		int posicaoComecoX = location.x + 1;
		int posicaoFimX = size.width + location.x - 1;
		int posicaoComecoY = location.y + 1;
		int posicaoFimY = size.height + location.y - 1;
		
		int margin = 20;
		
		// Arrastar muito proximo as bordas pode acionar menus indesejados
		if (posicaoComecoX < margin) posicaoComecoX = margin;
		if (posicaoComecoY < margin) posicaoComecoY = margin;
		if (posicaoFimX > windowSize.width - margin) posicaoFimX = windowSize.width - margin;
		if (posicaoFimY < windowSize.height - margin) posicaoFimY = windowSize.height - margin;
		
		switch(direcao) {
			case PARA_CIMA:
				pontoInicial = point(posicaoMetadeX, posicaoFimY);
				pontoFinal = point(posicaoMetadeX, posicaoComecoY);
				break;
			case PARA_BAIXO:
				pontoInicial = point(posicaoMetadeX, posicaoComecoY);
				pontoFinal = point(posicaoMetadeX, posicaoFimY);
				break;
			case PARA_DIREITA:
				pontoInicial = point(posicaoComecoX, posicaoMetadeY);
				pontoFinal = point(posicaoFimX, posicaoMetadeY);
				break;
			case PARA_ESQUERDA:
				pontoInicial = point(posicaoFimX, posicaoMetadeY);
				pontoFinal = point(posicaoComecoX, posicaoMetadeY);
				break;
		}
		
		deslizarDePara(pontoInicial, pontoFinal, velocidade);
	}
	
	/**
	 * Realiza o gesto de deslizar no device
	 * @param direcao Direção para onde será realizado o gesto
	 * @param velocidade
	 */
	public void deslizarTela(Direcao direcao, Velocidade velocidade, int porcentagemIniLargura, int porcentagemIniAltura) {
		PointOption<?> pontoInicial = null;
		PointOption<?> pontoFinal = null;
		
		switch(direcao) {
			case PARA_CIMA:
				pontoInicial = point(larguraTela()/100*porcentagemIniLargura, alturaTela()/100*porcentagemIniAltura);
				pontoFinal = point(larguraTela()/100*porcentagemIniLargura, 0);
				break;
			case PARA_BAIXO:
				pontoInicial = point(larguraTela()/100*porcentagemIniLargura, alturaTela()/100*porcentagemIniAltura);
				pontoFinal = point(larguraTela()/100*porcentagemIniLargura, alturaTela());
				break;
			case PARA_DIREITA:
				pontoInicial = point(larguraTela()/100*porcentagemIniLargura, alturaTela()/100*porcentagemIniAltura);
				pontoFinal = point(larguraTela(), alturaTela()/100*porcentagemIniAltura);
				break;
			case PARA_ESQUERDA:
				pontoInicial = point(larguraTela()/100*porcentagemIniLargura, alturaTela()/100*porcentagemIniAltura);
				pontoFinal = point(0, alturaTela()/100*porcentagemIniAltura);
				break;
		}
		
		deslizarDePara(pontoInicial, pontoFinal, velocidade);
	}
	
	/**
	 * Realiza o gesto de deslizar no device, a partir de um elemento informado
	 * @param direcao Direção para onde será realizado o gesto
	 * @param elemento Elemento que será o ponto de partida
	 */
	public void deslizarElemento(Direcao direcao, ElementoMobile elemento) {
		deslizarElemento(direcao, elemento, Velocidade.NORMAL);
	}
	
	/**
	 * Realiza o gesto de deslizar no device, a partir de um elemento informado
	 * @param direcao Direção para onde será realizado o gesto
	 * @param elemento Elemento que será o ponto de partida
	 * @param velocidade
	 */
	public void deslizarElemento(Direcao direcao, ElementoMobile elemento, Velocidade velocidade) {
		Point coordElemento = elemento.getMobileElement().getLocation();
		PointOption<?> pontoInicial = PointOption.point(coordElemento.getX(), coordElemento.getY());	
		PointOption<?> pontoFinal = null;
		switch(direcao) {
		case PARA_CIMA:
			pontoFinal = PointOption.point(coordElemento.getX(), 0);
			break;
		case PARA_BAIXO:
			pontoFinal = PointOption.point(coordElemento.getX(), alturaTela());
			break;
		case PARA_DIREITA:
			pontoFinal = PointOption.point(larguraTela(), coordElemento.getY());
			break;
		case PARA_ESQUERDA:
			pontoFinal = PointOption.point(0, coordElemento.getY());
			break;
		}
		deslizarDePara(pontoInicial, pontoFinal, velocidade);
	}
	
	/**
	 * Retorna a altura da tela do device
	 * @return altura
	 */
	public int alturaTela() {
		return driver
				.manage()
				.window()
				.getSize()
				.getHeight() - 1;
	}
	

	/**
	 * Retorna a largura da tela do device
	 * @return largura
	 */
	public int larguraTela() {
		return driver.manage().window().getSize().getWidth() - 1;
	}
	
	/**
	 * Realiza o gesto de deslizar no device, recebendo por parâmetro o ponto inicial e final
	 * @param pontoInicial 
	 * @param pontoFinal
	 */
	public void deslizarDePara(PointOption<?> pontoInicial, PointOption<?> pontoFinal, Velocidade velocidade) {
		int segundos = 0;
		switch(velocidade) {
		case DEVAGAR:
			segundos = 2000;
			break;
		case NORMAL:
			segundos = 500;
			break;
		case RAPIDO:
			segundos = 100;
			break;
		}
		
		actions
			.press(pontoInicial)
			.waitAction(waitOptions(ofMillis(segundos)))
			.moveTo(pontoFinal)
			.release()
			.perform();
	}
	
	public void clicarVoltar() {
		driver.navigate().back();
	}
}
