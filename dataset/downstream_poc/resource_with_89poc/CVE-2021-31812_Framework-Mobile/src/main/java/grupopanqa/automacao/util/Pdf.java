package grupopanqa.automacao.util;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;

import java.io.File;
import java.io.IOException;

/**
 * Classe com os metodos relacionados a criação, leitura e alteração de planilha
 * excel
 * 
 * @author 800041563
 *
 */
public class Pdf {

	PDDocument document;

	/**
	 * Realiza o carregamento da planilha PDF
	 * 
	 * @param caminhoArquivo Caminho completo do arquivo PDF
	 * @throws IOException
	 */
	public void carregarArquivo(String caminhoArquivo) {

		try {
			File file = new File(caminhoArquivo);
			document = PDDocument.load(file);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	/**
	 * Seleciona a planilha desejada pelo nome
	 * 
	 * @param nome Nome da planilha
	 * @throws IOException
	 */
	public void recuperarTexto() {
		
		try {
			PDFTextStripper pdfStripper;
			pdfStripper = new PDFTextStripper();
			String text;
			text = pdfStripper.getText(document);
			System.out.println(text);
			document.close();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

}
