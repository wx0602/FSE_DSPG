package grupopanqa.automacao.util;

import java.io.IOException;
import java.util.Map;

/**
 *Classe com os metodos referentes a Variavel de Ambiente
 * @author 800041563
 *
 */
public class VariavelAmbiente {
	static Process process;
	public static ProcessBuilder pb= new ProcessBuilder("CMD", "/C", "SET");
	/**
	 * Adiciona a chave e valor como variavel de ambiente
	 * @param chave
	 * @param valor
	 */
	public static void adicionarVariavel(String chave, String valor){
		try {
			Map<String, String> env = pb.environment();
			//Caso a variavel de ambiente ja exista, ela e removida e depois gerada com o novo valor
			if (env.get(chave) != null){
				env.remove(chave);
			}
			env.put(chave, valor);
			process = pb.start();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Metodo responsavel por recuperar o valor armazenado na variavel de ambiente
	 * @param chave
	 * @return
	 */
	public static String recuperarVariavel(String chave){
		String varAmbiente = pb.environment().get(chave);
		return varAmbiente;
	}	
	
	/**
	 * Finaliza as variaveis de ambiente que foram geradas via codigo
	 */
	public static void finalizarVariavel(){
		pb.environment().clear();
	}
}
