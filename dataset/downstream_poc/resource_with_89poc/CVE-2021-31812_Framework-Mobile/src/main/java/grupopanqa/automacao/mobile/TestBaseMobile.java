package grupopanqa.automacao.mobile;

import static grupopanqa.automacao.dados.ConfiguracaoDados.getReportPath;
import static grupopanqa.automacao.util.ReportExtentReports.adicionarLog;
import static grupopanqa.automacao.util.ReportExtentReports.adicionarSuiteTeste;
import static grupopanqa.automacao.util.ReportExtentReports.iniciarReport;
import static org.junit.Assert.fail;

import java.io.File;
import java.io.IOException;
import java.time.Instant;

import org.junit.Assert;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.TestInfo;

import grupopanqa.automacao.dados.ConfiguracaoDados;
import grupopanqa.automacao.util.ArquivoImagem;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.ReportExtentReports;
import grupopanqa.automacao.util.TestBase;
import grupopanqa.automacao.util.Util;
import grupopanqa.automacao.util.VariavelAmbiente;

/**
 * Classe que serve como base (extends) para todas as classes de teste mobile
 * Junit que irão usar o ExtentReports atualizado para JUNIT5
 * 
 * @author 800041563
 */
public class TestBaseMobile extends TestBase {

	static ConfiguracaoDados configFile = new ConfiguracaoDados();
	public Device device;
	/**
	 * Inicia o report e carregamento dos dados do arquivo device.json antes da execução dos testes
	 */
//	@BeforeAll
//	public static void beforeClass(TestInfo testInfo) {
//		//Realiza o carregamento dos dados do arquivo device.json
//		configFile = new ConfiguracaoDados();
//		String localJsonConfig = ParametersConfiguration.DEVICE_JSON.value();
//		ConfigMobile.carregaArquivo(localJsonConfig);
//
//		//Inicializa o report para inclusão de log e evidências
//		String diretorio = ConfigMobile.getDiretorioReport();
//		ReportExtentReports.iniciarReport(diretorio, "BancoDigitalReport");
//		ReportExtentReports.adicionarSuiteTeste(testInfo.getTestClass().get().getSimpleName(),
//				testInfo.getDisplayName());
//	}
	
	public TestBaseMobile() {
		
	}

	@BeforeAll
	
	public static void beforeClass(TestInfo testInfo) {
		
		String diretorio = getReportPath();
		iniciarReport(diretorio, "BancoDigitalReport");
		adicionarSuiteTeste(testInfo.getTestClass().get().getSimpleName(),testInfo.getDisplayName());
	}
	
	/**
	 * Cria um novo teste no ExtentsReport
	 * 
	 * @param testInfo Capturado automaticamente
	 */
	@BeforeEach
	public void beforeTest(TestInfo testInfo) {
		String nomeClasse = testInfo.getTestClass().get().getSimpleName();
		String nomeTeste = testInfo.getTestMethod().get().getName();
		String descricaoTeste = testInfo.getDisplayName();
		String thread_id = String.valueOf(Thread.currentThread().getId());
		ReportExtentReports.adicionarTeste(nomeClasse, thread_id, nomeTeste, descricaoTeste);
	}

	/**
	 * Depois da execução de cada teste, realiza a limpeza das variaveis de ambiente e finaliza o report
	 * e adiciona um registro no log do report
	 */
	@AfterEach
	public void afterTest() {
		VariavelAmbiente.finalizarVariavel();
		ReportExtentReports.finalizarTeste();
	}

	/**
	 * Finaliza o report após a execução de todos os testes
	 */
	@AfterAll
	public static void afterClass() {
		ReportExtentReports.finalizarReport();
		Util.zipReportFiles();
	}

	/**
	 * Adiciona registro no log de execução do report
	 * 
	 * @param status       Tipo de status que será adicionado no log (status FAIL
	 *                     irá falhar e interromper a execução do teste)
	 * @param descricao    Descrição do registro que será adicionado
	 * @param capturarTela Caso True, irá gerar um screenshot e adicionar no report
	 *                     junto com o registro
	 * @param device	   Device sendo utilizado na execução
	 */
	public static void logReport(Status status, String descricao, Boolean capturarTela, Device device) {
		String thread_id = String.valueOf(Thread.currentThread().getId());
		if (ReportExtentReports.reportInicializado) {
			//Verifica se é para tirar screen shot da tela
			if (capturarTela) {
				try {
					String evidencia = salvarScreenShot(device);
					//Caso evidencia esteja nula, provavelmente a tela do aplicativo possui bloqueio de segurança contra screen shot
					if (evidencia == null) {
						
						descricao = descricao
								+ " Obs: Nao foi possivel tirar print da tela. Possivel motivo - 'Make sure the 'LayoutParams.FLAG_SECURE' is not set for the current view'";
						String elementos_tela = device.getDriver().getPageSource().toString();
						//Adicionado mapeamento da tela, uma vez que não é possível tirar scree shot
						ReportExtentReports.adicionarLog(thread_id, status, descricao);
						//Necessário subistituição abaixo para que o código HTML seja exibido na evidência
						elementos_tela = elementos_tela.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
						ReportExtentReports.adicionarLog(thread_id, Status.INFO,
								"Elementos na tela: " + elementos_tela);
					} else {
						ReportExtentReports.adicionarLog(thread_id, status, descricao, salvarScreenShot(device));
					}

				} catch (IOException e) {
					Assert.fail("Erro ao armazenar log no ExtentReports: " + e);
				}
			} else {
				//Adiciona log sem evidência (sem screen shot)
				adicionarLog(thread_id, status, descricao);
			}
			//Caso o status seja FAIL, o teste falhará automaticamente
			if (status == Status.FAIL) {
				device.finalizar();
				
				fail(descricao);
			}
		} else {
			//Caso o teste falhe antes da inicialização do report, será possível apenas exibir log do erro na tela
			if (status == Status.FAIL) {
				System.err.println("Report nao foi inicializado. Log de erro: " + descricao);
				Assert.fail(descricao);
			}
			System.out.println("Report nao foi inicializado. Log: " + descricao);
		}

	}

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
				System.err.println("Report nao foi inicializado. Log de erro: " + descricao);
				Assert.fail(descricao);
			}
			System.out.println("Report nao foi inicializado. Log: " + descricao);
		}

	}

	/**
	 * Salvar screenShot e retorna o nome no formato para ser utilizado para anexo
	 * no ExtentReports
	 * 
	 * @return String Nome do arquivo gerado
	 */
	public static String salvarScreenShot(Device device) {
		String evidenciaId = Long.toString(Instant.now().toEpochMilli());
		String formatoImagem = "jpeg";
		String nomeCompletoEvidencia = getReportPath() + evidenciaId + "." + formatoImagem;
		File evidencia = ArquivoImagem.evidenciarTelaMobile(formatoImagem, nomeCompletoEvidencia, device);
		// Será retornado null caso não seja possível tirar print da tela da aplicação
		// mobile
		if (evidencia == null) return null;

		return evidenciaId + "." + formatoImagem;
	}
}
