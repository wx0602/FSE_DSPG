package grupopanqa.automacao.util;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class ArquivoValidacao {
	BufferedReader reader;
	int numeroLinha = 0;
	String textoLinhaAtual = "";



	/**
	 * Recebe o caminho de um arquivo (txt, json...)
	 * 
	 * @param caminhoArquivo Caminho do arquivo
	 */
	public ArquivoValidacao(String caminhoArquivo) {
		try {
			reader = new BufferedReader(new FileReader(caminhoArquivo));
		} catch (IOException e) {
			e.printStackTrace();
		}

	}
	
	public String retornaTextoProximaLinha() {
		textoLinhaAtual = null;
		try {
			textoLinhaAtual = reader.readLine();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		numeroLinha ++;
		return textoLinhaAtual;
		
	}
	
	public int getNumeroLinha() {
		return numeroLinha;
	}
}
