package grupopanqa.automacao.util;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

import java.util.ArrayList;
import java.util.List;

/**
 * Classe responsável por prover os metodos referentes a SMS mobile
 * 
 * @author 42289911810
 *
 */
public class SMS_versaoWeb {

	private static final String urlSmsOnline = "https://sms-online.co/receive-free-sms/";
	private String primeiroCodigo = "";
	
	String numeroReceptor = "";
	public SMS_versaoWeb(String numeroReceptor) {
		this.numeroReceptor = numeroReceptor;
	}

	/**
	 * Metodo para retornar a lista de SMS de um determinado numero
	 * 
	 * @param numero Numero de destino (ex: numero americano 12018577757)
	 * @return Lista de elementos (sms)
	 */
	private List<Element> retornaListaSMS() {
		List<Element> elementos = new ArrayList<>();
		try {
			Document documento = Jsoup.connect(urlSmsOnline + numeroReceptor).validateTLSCertificates(false).get();
			elementos = documento.getElementsByClass("list-item-content break-word");
		} catch (Exception erro) {
			System.out.println("Erro: " + erro);
		}
		return elementos;
	}

	/**
	 * Filtra a lista de elementos atraves de texto informado por parametro e retorna o primeiro elemento encontrado
	 * @param elementos Lista de elementos
	 * @param filtro Texto a ser utilizado para filtrar
	 * @return Elemento com o texto
	 */
	private  Element filtraListaElementos(List<Element> elementos, String filtro) {
		Element elemento = null;
		if(elementos.size() > 0) {
			for (Element el : elementos) {
				if (el.text().contains(filtro)) {
					elemento = el;
					break;
				}
			}
		}
		return elemento;

	}

	/**
	 * Retorna apenas o codigo do APP Banco Digital
	 * @param numero Numero de destino (ex: numero americano 12018577757) 
	 * @return Texto com o codigo encontrado
	 */
	public String retornaCodigoSMSBancoDigital() {
		String codigo = "";
		Element sms = filtraListaElementos(retornaListaSMS(), "Banco PAN");
		if(sms != null) {
	    	int cont = sms.text().indexOf("codigo para validacao: ");
	    	System.out.println("Mensagem original encontrada: " + sms.text());
			codigo = sms.text().substring(cont+23, cont + 29);
		}

		return codigo;
	}

	/**
	 * Armazena o código antigo, antes do envio de um novo SMS para comparação e saber que é um novo SMS
	 * @return
	 */
	public String armazenaCodigoAntigoSMSBancoDigital() {
		primeiroCodigo = retornaCodigoSMSBancoDigital();
		System.out.println("Primeiro código encontrado: " + primeiroCodigo);
		return primeiroCodigo;
	}
	
	/**
	 * Realiza uma primeira consulta e aguarda ate que um novo codigo seja encontrado
	 * @param numero Numero de destino (ex: numero americano 12018577757) 
	 * @return Texto com o novo codigo encontrado | Caso nao seja encontrado um novo codigo, sera devolvido texto vazio
	 */
	public String aguardarNovoCodigoSMSBancoDigital() {
		String codigoNovo = "";
		for(int cont = 0; cont < 180; cont ++) {
			System.out.println("Aguardando novo codigo no SMS...");
			codigoNovo = retornaCodigoSMSBancoDigital();
			if (!primeiroCodigo.equals(codigoNovo) && codigoNovo != "") {
				System.out.println("Novo codigo encontrado: " + codigoNovo);
				return codigoNovo;
			}
		}
		System.out.println("Nao foi encontrado um novo codigo.");
		return "";
	}
	
}
