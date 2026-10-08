package grupopanqa.automacao.util;

public class Tempo {
	/**
	 * Aguardar segundos
	 * @param segundos Quantidade de segundos
	 * @return
	 */
	public static void aguardarSegundos(int segundos) {
		try {
			Thread.sleep(segundos * 1000);
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
}
