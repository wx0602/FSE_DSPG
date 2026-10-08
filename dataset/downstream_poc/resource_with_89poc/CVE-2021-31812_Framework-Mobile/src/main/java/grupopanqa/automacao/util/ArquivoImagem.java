package grupopanqa.automacao.util;

import grupopanqa.automacao.mobile.Device;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.web.Navegador;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriverException;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

/**
 * Classe com metodos que auxiliam na automação de imagens (jpeg, buffered, printscreen...)
 * @author 800041563
 *
 */
public class ArquivoImagem {

	/**
	 * Tira o PrintScreen da tela e salva a imagem em um arquivo
	 * @param formato Formato do arquivo ex: jpg, png...
	 * @param caminhoArquivo Caminho completo de como sera salvo o arquivo (com extensao)
	 * @return File Retorna o arquivo do PrintScreen
	 */
	public static File evidenciarTelaDesktop(String formato, String caminhoArquivo) {
		File arquivoEvidencia = null;
		try {

			Robot robot = new Robot();
			arquivoEvidencia = new File(caminhoArquivo);

			Rectangle screenRect = new Rectangle(Toolkit.getDefaultToolkit().getScreenSize());
			BufferedImage screenFullImage = robot.createScreenCapture(screenRect);
			ImageIO.write(diminuirImagem(screenFullImage, 0.9), formato, arquivoEvidencia);

		} catch (AWTException | IOException e) {
			TestBase.logReport(Status.FAIL, "Erro ao evidenciar a tela no arquivo: " + caminhoArquivo + ". Erro: " + e);
		}
		return arquivoEvidencia;
	}
	
	/**
	 * Tira o PrintScreen do navegador e salva a imagem em um arquivo
	 * @param formato
	 * @param caminhoArquivo
	 * @param navegador
	 * @return File Retorna o arquivo do PrintScreen
	 */
	public static File evidenciarTelaNavegador(String formato, String caminhoArquivo, Navegador navegador) {
		File file = null;

		try {
			file = ((TakesScreenshot) navegador.getDriver()).getScreenshotAs(OutputType.FILE);
			BufferedImage in = ImageIO.read(file);
			BufferedImage in_reduzida = diminuirImagem(in, 1);
			ImageIO.write(in_reduzida, formato, new File(caminhoArquivo));

		} catch (IOException e) {
			TestBase.logReport(Status.FAIL, "Erro ao evidenciar a tela no arquivo: " + caminhoArquivo + ". Erro: " + e);
		}
		return file;
	}

	/**
	 * Tira o PrintScreen da tela mobile e salva a imagem em um arquivo
	 * 
	 * @param formato        Formato do arquivo ex: jpg, png...
	 * @param caminhoArquivo Caminho completo de como sera salvo o arquivo (com extensao)
	 * @param device Device a ser tirado printscreen
	 * @return File Retorna o arquivo do PrintScreen
	 */
	public static File evidenciarTelaMobile(String formato, String caminhoArquivo, Device device) {
		File file = null;

		try {
			file = ((TakesScreenshot) device.getDriver()).getScreenshotAs(OutputType.FILE);
			BufferedImage in = ImageIO.read(file);
			BufferedImage in_reduzida = diminuirImagem(in, 0.3);
			ImageIO.write(in_reduzida, formato, new File(caminhoArquivo));

		} catch (WebDriverException e) {
			// Caso seja exibido a exception abaixo, a tela do app não permite tirar
			// screenshot
			if (e.getLocalizedMessage().contains("The size of the taken screenshot equals to zero.")) {
				return null;
			}
		} catch (IOException e) {
			TestBase.logReport(Status.FAIL, "Erro ao evidenciar a tela no arquivo: " + caminhoArquivo + ". Erro: " + e);
		}
		return file;
	}
	
	/**
	 * Diminui a imagem de acordo com a porcentagem informada
	 * @param img BufferedImage a ser diminuida
	 * @param porcentagem Porcentagem da nova imagem em relação à original
	 * @return Imagem BufferedImage reduzida
	 */
    private static BufferedImage diminuirImagem(BufferedImage img, double porcentagem) {
    	
        int scaledWidth = (int) (img.getWidth() * porcentagem);
        int scaledHeight = (int) (img.getHeight() * porcentagem);
    	
        Image tmp = img.getScaledInstance(scaledWidth, scaledHeight, Image.SCALE_SMOOTH);
        
        BufferedImage imagemReduzida = new BufferedImage(scaledWidth, scaledHeight, BufferedImage.SCALE_DEFAULT);
        Graphics2D g2d = imagemReduzida.createGraphics();
        g2d.drawImage(tmp, 0, 0, null);
        g2d.dispose();
        return imagemReduzida;
    }
	
}
