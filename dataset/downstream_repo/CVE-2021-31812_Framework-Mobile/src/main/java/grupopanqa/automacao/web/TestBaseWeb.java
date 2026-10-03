package grupopanqa.automacao.web;

import grupopanqa.automacao.dados.ConfiguracaoDados;
import grupopanqa.automacao.util.ArquivoImagem;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.ReportExtentReports;
import grupopanqa.automacao.util.TestBase;
import grupopanqa.automacao.util.VariavelAmbiente;
import org.junit.Assert;
import org.junit.jupiter.api.*;

import java.io.IOException;
import java.time.Instant;

/**
 * Classe que serve como base (extends) para todas as classes de teste Junit que irão usar o ExtentReports
 * Atualizado para JUNIT5
 * @author 800041563
 */
public class TestBaseWeb extends TestBase{
	
	static ConfiguracaoDados configFile;
	
	/**
	 * Inicia o report antes da execução dos testes
	 */
	//@BeforeClass
	@BeforeAll
	public static void beforeClass(TestInfo testInfo){
		configFile = new ConfiguracaoDados();
		String diretorio = configFile.recuperarValor("REPORTPATH");
		ReportExtentReports.iniciarReport(diretorio, "AutomacaoGrupoPan");
		ReportExtentReports.adicionarSuiteTeste(testInfo.getTestClass().get().getSimpleName(),testInfo.getDisplayName());
	}

	/**
	 * Cria um novo teste no ExtentsReport
	 * @param testInfo Capturado automaticamente
	 */
	@BeforeEach
	public void beforeTest(TestInfo testInfo){
		String nomeClasse = testInfo.getTestClass().get().getSimpleName();
		String nomeTeste = testInfo.getTestMethod().get().getName();
		String descricaoTeste = testInfo.getDisplayName();
		String thread_id = String.valueOf(Thread.currentThread().getId());
		ReportExtentReports.adicionarTeste(nomeClasse, thread_id, nomeTeste, descricaoTeste);
	}		
	
	/**
	 * Depois da execução de cada teste, realiza a limpeza das variaveis de ambiente e adiciona um registro no log do report
	 */
	@AfterEach
	public void afterTest(){
		VariavelAmbiente.finalizarVariavel();
		ReportExtentReports.finalizarTeste();
	}	
	
	/**
	 * Finaliza o report após a execução de todos os testes
	 */
	@AfterAll
	public static void afterClass(){
		ReportExtentReports.finalizarReport();
	}
		
	/**
	 * Adiciona registro no log de execução do report
	 * @param status Tipo de status que será adicionado no log (status FAIL irá falhar e interromper a execução do teste)
	 * @param descricao Descrição do registro que será adicionado
	 * @param capturarTela Caso True, irá gerar um screenshot e adicionar no report junto com o registro
	 */
	public static void logReport(Status status, String descricao, Boolean capturarTela, Navegador navegador){
		String thread_id = String.valueOf(Thread.currentThread().getId());
		if(ReportExtentReports.reportInicializado) {
			if(capturarTela){
				try {
					ReportExtentReports.adicionarLog(thread_id, status,descricao, salvarScreenShot(navegador));
				} catch (IOException e) {
					Assert.fail("Erro ao armazenar log no ExtentReports: " + e);
				}
			}else{
				ReportExtentReports.adicionarLog(thread_id, status,descricao);
			}
			if (status == Status.FAIL){
				Assert.fail(descricao);
			}
		}
		else {
			if (status == Status.FAIL){
				System.err.println("Report não foi inicializado. Log de erro: " + descricao);
				Assert.fail(descricao);
			}
			System.out.println("Report não foi inicializado. Log: " + descricao);
		}

	}
	/**
	 * Salvar screenShot e retorna o nome no formato para ser utilizado para anexo no ExtentReports
	 * @return String Nome do arquivo gerado
	 */
	public static String salvarScreenShot(Navegador navegador){
		String evidenciaId = Long.toString(Instant.now().toEpochMilli());
		String formatoImagem = "jpeg";
		String nomeCompletoEvidencia = configFile.recuperarValor("REPORTPATH") + evidenciaId + "." + formatoImagem;
		ArquivoImagem.evidenciarTelaNavegador(formatoImagem, nomeCompletoEvidencia, navegador).toString();
		return evidenciaId + "." + formatoImagem;
	}
}
