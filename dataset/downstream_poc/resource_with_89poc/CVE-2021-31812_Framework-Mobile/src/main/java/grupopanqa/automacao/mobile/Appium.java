package grupopanqa.automacao.mobile;

import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.Processos;
import grupopanqa.automacao.util.Tempo;
import grupopanqa.automacao.util.TestBase;
import org.apache.commons.exec.CommandLine;
import org.apache.commons.exec.DefaultExecuteResultHandler;
import org.apache.commons.exec.DefaultExecutor;
import org.apache.commons.exec.PumpStreamHandler;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;

/**
 * Classe responsável pela gestão da conexão com o Appium para testes mobile
 * Recomendado abrir uma porta para cada teste mobile em caso de testes em
 * paralelo
 * 
 * @author 800041563
 *
 */
public class Appium {

	String instanciaPorta = "";

	/**
	 * Realiza uma nova conexão com o Appium (
	 * 
	 * @param porta Numero da porta a ser utilizada pelo Appium
	 * @param localAppiumJS Local aonde se encontra o main.js do Appium
	 * @param servidorIp Ex: 0.0.0.0
	 * @param localNodeExe Local aonde se encontra o exe do Node
	 */
	public void iniciarAppium(int porta, String localAppiumJS, String servidorIp, String localNodeExe) {

		instanciaPorta = Integer.toString(porta);

		CommandLine cmd = new CommandLine(localNodeExe);

		cmd.addArgument(localAppiumJS);
		cmd.addArgument("--address");
		cmd.addArgument(servidorIp);
		cmd.addArgument("--port");
		cmd.addArgument(instanciaPorta);
		cmd.addArgument("--relaxed-security");

		ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
		PumpStreamHandler streamHandler = new PumpStreamHandler(outputStream);

		DefaultExecuteResultHandler handler = new DefaultExecuteResultHandler();
		DefaultExecutor executor = new DefaultExecutor();

		executor.setStreamHandler(streamHandler);
		executor.setExitValue(1);
		try {
			//Verifica se há um serviço utilizando a porta
			if(verificaPortaOcupada(instanciaPorta)) {
				TestBase.logReport(Status.INFO, "Porta em uso, finalizando: " + porta );
				finalizarInstancia();
			}
			TestBase.logReport(Status.INFO, "Enviado comando: " + cmd );
			executor.execute(cmd, handler);
			aguardarServicoFicarDisponivel(instanciaPorta, 40);
			TestBase.logReport(Status.INFO, "Realizada a conexão com o appium: " + outputStream.toString());
		} catch (IOException e) {
			TestBase.logReport(Status.FAIL, "Falha ao realizar inicialização do Appium pela porta " + porta + ". Erro: " + e);
		}
	}



	
	/**
	 * Aguarda a porta ficar ocupada para validar que o serviço está rodando
	 * 
	 * @param porta Número da porta
	 * @param timeoutSegundos Tempo de espera para o servico ficar disponiível (porta ocupada)
	 */
	private void aguardarServicoFicarDisponivel(String porta, int timeoutSegundos) {
		int contAguardandoProcesso = 0;
		while (!verificaPortaOcupada(porta)) {
			Tempo.aguardarSegundos(1);
			contAguardandoProcesso++;
			if (contAguardandoProcesso > timeoutSegundos) {
				TestBase.logReport(Status.FAIL,
						"Porta " + porta + " não ficou ativo após aguardar " + timeoutSegundos + " segundos");
			}
		}
	}

	/**
	 * Aguarda a porta ficar livre (sem uso)
	 * 
	 * @param porta Número da porta
	 * @param timeoutSegundos Tempo de espera para a porta ficar livre (sem utilização)
	 */
	private void aguardarPortaFicarLivre(String porta, int timeoutSegundos) {
		int contAguardandoProcesso = 0;
		while (verificaPortaOcupada(porta)) {
			Tempo.aguardarSegundos(1);
			contAguardandoProcesso++;
			if (contAguardandoProcesso > timeoutSegundos) {
				TestBase.logReport(Status.FAIL,
						"Porta " + porta + " não ficou disponivel para uso após aguardar " + timeoutSegundos + " segundos");
			}
		}
	}
	
	/**
	 * Verifica se a porta esta ocupada (verificado que nao funciona em sistema mac osx
	 * 
	 * @param porta Número da porta
	 * @return Boolean true (em uso) / false (não está em uso)
	 */
	@Deprecated
	private boolean verificaPortaEmUso(String porta) {

		boolean portaEmUso = false;
		ServerSocket serverSocket;
		//Socket socket = new Socket("localhost", 2111);
		
		//ServerSocket serverSocket2;
		try {
			//InetAddress addr = new InetAddress();
			serverSocket = new ServerSocket	(Integer.parseInt(porta));
			//serverSocket2 = new ServerSocket(Integer.parseInt(porta));
			System.out.println(serverSocket.isClosed());
			serverSocket.close();
		} catch (Exception e) {
			portaEmUso = true;
		} finally {
			serverSocket = null;
		}
		return portaEmUso;
	}

	
	/**
	 * Verifica se a porta esta ocupada
	 * 
	 * @param porta Número da porta
	 * @return Boolean true (em uso) / false (não está em uso)
	 */
	private boolean verificaPortaOcupada(String porta) {
		
	    System.out.println("Testando porta " + porta);
	    Socket s = null;
	    try {
	        s = new Socket("localhost", Integer.parseInt(porta));
	        System.out.println("Porta " + porta + " nao esta disponivel");
	        return true;
	    } catch (IOException e) {
	        System.out.println("Porta " + porta + " esta disponivel");
	        return false;
	    } finally {
	        if( s != null){
	            try {
	                s.close();
	            } catch (IOException e) {
	                throw new RuntimeException("Erro ao tentar fechar a porta:" , e);
	            }
	        }
	    }
	}
	
	/**
	 * Finaliza todos os processos node.exe (finaliza assim todas as instancias do Appium abertas)
	 */
	public static void finalizarTodasInstancias() {
		Processos.finalizarProcesso("node.exe");
	}
	
	/**
	 * Finaliza a instancia do Appium
	 */
	public void finalizarInstancia() {
		String pid = Processos.retornaProcessoPID(instanciaPorta);
		if (pid != "") {
			Processos.finalizarProcessoPeloPID(pid);
			aguardarPortaFicarLivre(instanciaPorta, 20);
		}
	}
}
