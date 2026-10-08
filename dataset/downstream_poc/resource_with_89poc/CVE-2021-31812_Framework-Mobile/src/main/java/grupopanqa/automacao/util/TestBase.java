package grupopanqa.automacao.util;

import grupopanqa.automacao.util.EnumFramework.Status;
import org.junit.Assert;

/**
 * Classe que serve como base (extends) para todas as classes de teste Junit que irão usar o ExtentReports
 * Atualizado para JUNIT5
 * @author 800041563
 */
public class TestBase{
	
	/**
	 * Adiciona registro no log de execução do report quando não há device
	 * @param status       Tipo de status que será adicionado no log (status FAIL
	 *                     irá falhar e interromper a execução do teste)
	 * @param descricao    Descrição do registro que será adicionado
	 */
	public static void logReport(Status status, String descricao) {
		String thread_id = String.valueOf(Thread.currentThread().getId());
		if (ReportExtentReports.reportInicializado) {
			ReportExtentReports.adicionarLog(thread_id, status, descricao);
			if (status == Status.FAIL) {
				Assert.fail(descricao);
			}
		} else {
			if (status == Status.FAIL) {
				System.err.println("Report não foi inicializado. Log de erro: " + descricao);
				Assert.fail(descricao);
			}
			System.out.println("Report não foi inicializado. Log: " + descricao);
		}

	
	}
}
