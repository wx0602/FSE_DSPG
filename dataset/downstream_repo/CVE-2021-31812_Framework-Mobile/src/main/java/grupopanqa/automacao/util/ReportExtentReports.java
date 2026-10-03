package grupopanqa.automacao.util;

import com.aventstack.extentreports.ExtentReports;
import com.aventstack.extentreports.ExtentTest;
import com.aventstack.extentreports.MediaEntityBuilder;
import com.aventstack.extentreports.Status;
import com.aventstack.extentreports.reporter.ExtentSparkReporter;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Classe responsavel por criar e manipular o arquivo de report
 * 
 * @author 800041563
 *
 */
public class ReportExtentReports {

	public static ExtentReports extent;
	public static ExtentTest suiteTeste;
	public static ExtentSparkReporter htmlReporter;
	public static Boolean reportInicializado = false;

	static Map<String, ExtentTest> lista_classes_teste = new HashMap<String, ExtentTest>(); //Lista de classes de testes - necessário para testes paralelos
	static Map<String, ExtentTest> lista_testes = new HashMap<String, ExtentTest>(); //Lista de testes - necessário para testes paralelos

	/**
	 * Inicializa o report (apenas uma vez)
	 * 
	 * @param diretorioReport Diretorio aonde sera armazenado o report (caso nao
	 *                        exista, o diretorio sera criado)
	 * @param nomeReport      Nome do report HTML (sem extensao)
	 */
	public synchronized static void iniciarReport(String diretorioReport, String nomeReport) {

		// Verifica se o report já foi inicializado
		if (!reportInicializado) {
			extent = new ExtentReports();
			File diretorioEvidencia = new File(diretorioReport);
			if (!diretorioEvidencia.exists()) {
				diretorioEvidencia.mkdirs();
			}
			htmlReporter = new ExtentSparkReporter(diretorioReport + nomeReport + ".html");
			//htmlReporter.setAppendExisting(true);
			htmlReporter.config().setDocumentTitle("Report de execucao");
			htmlReporter.config().setReportName("Automacao Grupo Pan");
			extent.attachReporter(htmlReporter);
			reportInicializado = true;

		}

	}

	/**
	 * Finaliza o teste
	 */
	public static void finalizarTeste() {
		// extent.flush();
	}

	/**
	 * Salva os dados do report
	 */
	public static void finalizarReport() {
		extent.flush();
	}

	/**
	 * Adiciona uma nova suite de teste no report
	 * 
	 * @param nomeTeste      Nome da suite de teste
	 * @param descricaoTeste Descricao da suite de teste
	 */
	public static void adicionarSuiteTeste(String nomeClasseTeste, String descricaoTeste) {
		lista_classes_teste.put(nomeClasseTeste, extent.createTest(nomeClasseTeste, descricaoTeste));
	}

	/**
	 * Adiciona um novo teste na suite do report
	 * 
	 * @param nomeTeste      Nome do teste
	 * @param descricaoTeste Descricao do teste
	 */
	public static void adicionarTeste(String nomeClasseTeste, String thread_id, String nomeTeste,
			String descricaoTeste) {
		suiteTeste = lista_classes_teste.get(nomeClasseTeste);
		ExtentTest teste = suiteTeste.createNode(nomeTeste, descricaoTeste);
		lista_testes.put(thread_id, teste);
	}

	/**
	 * Adiciona status e log de registro no caso de teste com evidencia
	 * 
	 * @param status     Enum do Status
	 * @param descricao  Descricao do log
	 * @param screenShot Nome da evidencia a ser anexado (deve estar na mesma pasta
	 *                   do report)
	 * @throws IOException
	 */
	public static void adicionarLog(String thread_id, grupopanqa.automacao.util.EnumFramework.Status status,
			String descricao, String screenShot) throws IOException {
		ExtentTest teste = lista_testes.get(thread_id);
		
		teste.log(conversorStatus(status), descricao,
				MediaEntityBuilder.createScreenCaptureFromPath(screenShot).build());
		//System.out.println(descricao);
	}

	/**
	 * Adiciona status e log de registro no caso de teste sem evidencia
	 * 
	 * @param status    Enum do Status
	 * @param descricao Descricao do log
	 */
	public static void adicionarLog(String thread_id, grupopanqa.automacao.util.EnumFramework.Status status,
			String descricao) {
		ExtentTest teste = lista_testes.get(thread_id);
		teste.log(conversorStatus(status), descricao);
		//System.out.println(descricao);
	}

	/**
	 * Converte o status do framework para o status que é utilizado pela biblioteca
	 * ExtentReports
	 * 
	 * @param status Enum do status a ser convertido
	 * @return Status convertido
	 */
	private static Status conversorStatus(grupopanqa.automacao.util.EnumFramework.Status status) {

		Status reportStatus = null;
		switch (status) {
//		case DEBUG:
//			reportStatus = Status.DEBUG;
//			break;
//		case ERROR:
//			reportStatus = Status.ERROR;
//			break;
		case FAIL:
			reportStatus = Status.FAIL;
			break;
//		case FATAL:
//			reportStatus = Status.FATAL;
//			break;
		case INFO:
			reportStatus = Status.INFO;
			break;
		case PASS:
			reportStatus = Status.PASS;
			break;
		case SKIP:
			reportStatus = Status.SKIP;
			break;
		case WARNING:
			reportStatus = Status.WARNING;
			break;
		}

		return reportStatus;

	}

}