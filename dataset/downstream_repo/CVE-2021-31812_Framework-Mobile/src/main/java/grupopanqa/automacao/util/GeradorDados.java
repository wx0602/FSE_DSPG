package grupopanqa.automacao.util;

import javax.swing.text.MaskFormatter;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class GeradorDados {
	private static ArrayList<Integer> listaAleatoria;
	private static ArrayList<Integer> listaNumMultiplicados = null;
	
	public static int geraNumAleatorio(int minimo, int maximo){
	    //Note que foi preciso fazer um cast para int, ja que Math.random() retorna um double
	    //int numero = (int) (Math.random() * 10);
		Random gerador = new Random();
		int numero = gerador.nextInt(maximo - minimo + 1);
		numero = numero + minimo;
	    return numero;
	}
	
	private static ArrayList<Integer> geraCPFParcial(){
		listaAleatoria = new ArrayList<Integer>();
	    for(int i = 0; i < 9; i++){
	        listaAleatoria.add(geraNumAleatorio(0,9));
	    }
	    return listaAleatoria;
	}

	//Metodo para geracao do primeiro digito verificador (para isso nos baseamos nos 9 digitos aleatorios gerados anteriormente)
	private static ArrayList<Integer> geraPrimeiroDigito(){
	    listaNumMultiplicados = new ArrayList<Integer>();
	    int primeiroDigito;
	    int totalSomatoria = 0;
	    int restoDivisao;
	    int peso = 10;
	    //Para cada item na lista multiplicamos seu valor pelo seu peso
	    for(int item : listaAleatoria){
	        listaNumMultiplicados.add(item * peso);
	        peso--;
	    }
	    //Agora somamos todos os itens que foram multiplicados
	    for(int item : listaNumMultiplicados){
	        totalSomatoria += item;
	    }
	        restoDivisao = (totalSomatoria % 11);
	    //Se o resto da divisao for menor que 2 o primeiro digito sera 0, senao subtraimos o numero 11 pelo resto da divisao
	    if(restoDivisao < 2){
	        primeiroDigito = 0;
	    } else{
	        primeiroDigito = 11 - restoDivisao;
	    }
	    //Apos gerar o primeiro digito o adicionamos a lista
	    listaAleatoria.add(primeiroDigito);
	    return listaAleatoria;
	}
	//Metodo para geracao do segundo digito verificador (para isso nos baseamos nos 9 digitos aleatorios + o primeiro digito verificador)
	private static ArrayList<Integer> geraSegundoDigito(){
	    listaNumMultiplicados = new ArrayList<Integer>();
	    int segundoDigito;
	    int totalSomatoria = 0;
	    int restoDivisao;
	    int peso = 11;
	    //Para cada item na lista multiplicamos seu valor pelo seu peso (observe que com o aumento da lista o peso tambem aumenta)
	    for(int item : listaAleatoria){
	        listaNumMultiplicados.add(item * peso);
	        peso--;
	    }
	    //Agora somamos todos os itens que foram multiplicados
	    for(int item : listaNumMultiplicados){
	        totalSomatoria += item;
	    }
	    restoDivisao = (totalSomatoria % 11);
	    //Se o resto da divisao for menor que 2 o segundo digito sera 0, senao subtraimos o numero 11 pelo resto da divisao
	    if(restoDivisao < 2){
	        segundoDigito = 0;
	    } else{
	        segundoDigito = 11 - restoDivisao;
	    }
	    //Apos gerar o segundo digito o adicionamos a lista
	    listaAleatoria.add(segundoDigito);
	    return listaAleatoria;
	}
	
	//Agora que temos nossa lista com todos os digitos que precisamos vamos formatar os valores de acordo com a mascara do CPF
	public static String gerarCPF(Boolean comMascara) {
	    //Primeiro executamos os metodos de geracao
	    geraCPFParcial();
	    geraPrimeiroDigito();
	    geraSegundoDigito();
	    String cpf = "";
	    String texto = "";
	    /*Aqui vamos concatenar todos os valores da lista em uma string.
	    Por que isso? Porque a formatacao que o ArrayList gera me impossibilitaria de usar a mascara, pois junto com os numeros gerados ele tambem gera caracteres especias. Ex.: a saída de uma lista de inteiros (de 1 a 5) seria essa:
	    [1 , 2 , 3 , 4 , 5]
	    Dessa forma o sistema geraria a excecao ParseException*/
	    for(int item : listaAleatoria){
	        texto += item;
	    }
	    
	    if (comMascara) {
		    try{
		        MaskFormatter mf = new MaskFormatter("###.###.###-##");
		        mf.setValueContainsLiteralCharacters(false);
		        cpf = mf.valueToString(texto);
		    }catch(Exception ex){
		        ex.printStackTrace();
		    }
	    }
	    else {
	    	cpf = texto;
	    }
	    
	    //Dentro do bloco try.. catch.. tentaremos adicionar uma mascara ao nosso CPF

	return cpf;
	}
	
	/**
	 * Metodo que gera o numero de conta corrente com digito verificador. Utilizado para os testes de performance de conta corrente do AutBank
	 * Fixado agencia 00019 e prefixo 21 (range reservado para conta corrente)
	 * @return String Numero da conta corrente
	 */
	@SuppressWarnings("unchecked")
	public static String geradorConta() {

		@SuppressWarnings("rawtypes")
		List listaAleatoria = new ArrayList();
		@SuppressWarnings("rawtypes")
		List listaNumMultiplicados = null;

		listaAleatoria.add(0);
		listaAleatoria.add(0);
		listaAleatoria.add(0);
		listaAleatoria.add(1);
		listaAleatoria.add(9);
		listaAleatoria.add(2);
		listaAleatoria.add(1);

		// Primeiro executamos os metodos de geracao
//		for (int i = 0; i < 7; i++) {
//			listaAleatoria.add((int) (Math.random() * 10));
//		}

		String dataAtual = Instant.now().toString();
		System.out.println(dataAtual);
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(14, 15)));
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(15, 16)));
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(17, 18)));
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(18, 19)));
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(20, 21)));
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(21, 22)));
		listaAleatoria.add(Integer.parseInt(dataAtual.substring(22, 23)));
		
		
		listaNumMultiplicados = new ArrayList<Object>();
		int primeiroDigito;
		int totalSomatoria = 0;
		int restoDivisao;
		int peso = 2;

		// Para cada item na lista multiplicamos seu valor pelo seu peso
		for (int i = listaAleatoria.size()-1 ; i >=0  ; i--) {
			listaNumMultiplicados.add((Integer)listaAleatoria.get(i) * peso);
			if (peso == 9){
				peso = 2;
			}
			else{
				peso++;
			}
		}

		// Agora somamos todos os itens que foram multiplicados
		for (int i = 0 ; i < listaNumMultiplicados.size() ; i++) {
			totalSomatoria += (Integer)listaNumMultiplicados.get(i);
		}
		restoDivisao = (totalSomatoria % 11);

		// Se o resto da divisao for menor que 2 o primeiro digito sera 0, senao
		// subtraimos o numero 11 pelo resto da divisao
		if (restoDivisao < 2) {
			primeiroDigito = 0;
		} else {
			primeiroDigito = 11 - restoDivisao;
		}

		// Apos gerar o primeiro digito o adicionamos a lista
		listaAleatoria.add(primeiroDigito);

		String conta = "";
		String texto = "";

		/*
		 * Aqui vamos concatenar todos os valores da lista em uma string. Por
		 * que isso? Porque a formatacao que o ArrayList gera me
		 * impossibilitaria de usar a mascara, pois junto com os numeros gerados
		 * ele tambem gera caracteres especias. Ex.: a saída de uma lista de
		 * inteiros (de 1 a 5) seria essa: [1 , 2 , 3 , 4 , 5] Dessa forma o
		 * sistema geraria a excecao ParseException
		 */
		for (int i = 0 ; i < listaAleatoria.size() ; i++) {
			texto += listaAleatoria.get(i);
		}

		// Dentro do bloco try.. catch.. tentaremos adicionar uma mascara ao
		// nosso CPF
		try {
			//MaskFormatter mf = new MaskFormatter("###.###.###-##");
			//mf.setValueContainsLiteralCharacters(false);
			//cpf = mf.valueToString(texto);
			conta = texto;
		} catch (Exception ex) {
			ex.printStackTrace();
		}

		return conta;
	}
	
}
