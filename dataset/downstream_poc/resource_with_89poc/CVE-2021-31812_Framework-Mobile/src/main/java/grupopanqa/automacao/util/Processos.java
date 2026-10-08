package grupopanqa.automacao.util;

import grupopanqa.automacao.util.EnumFramework.Status;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Scanner;

public class Processos {
	public static boolean verificaEstaAtivo(String processoNome) {
		String tasksList = "";
		try {
			ProcessBuilder processBuilder = new ProcessBuilder("tasklist.exe");
			Process process = processBuilder.start();
			tasksList = leituraProcessos(process.getInputStream());
		} catch (Exception e) {
			TestBase.logReport(Status.FAIL,
					"Erro ao pesquisar se o processo " + processoNome + " esta ativo. Erro: " + e);
		}
		return tasksList.contains(processoNome);
	}

	private static String leituraProcessos(InputStream inputStream) {
		@SuppressWarnings("resource")
		Scanner scanner = new Scanner(inputStream, "UTF-8").useDelimiter("\\A");
		String string = scanner.hasNext() ? scanner.next() : "";
		scanner.close();

		return string;
	}

	public static void finalizarProcesso(String processoNome) {
		try {
			while (verificaEstaAtivo(processoNome)) {
				Runtime.getRuntime().exec("taskkill /F /IM " + processoNome);
				Thread.sleep(500);
			}

		} catch (Exception e) {
			TestBase.logReport(Status.FAIL, "Erro ao finalizar o processo " + processoNome + ". Erro: " + e);
		}
	}
	/**
	 * Retorna o PID do processo de acordo com a porta utilizada
	 * 
	 * @param porta do processo a ser buscado o PID
	 * @return pid
	 * @throws IOException
	 */
	public static String retornaProcessoPID(String porta) {
		String OS = System.getProperty("os.name");
		String comando = "";
		if (OS.contains("Mac")) {
			comando = "lsof -n -i4TCP:" + porta;
		}
		else {
			comando = "netstat -ano | findstr " + porta;
		}
		String pid = "";
		try {
			Runtime rt = Runtime.getRuntime();
			Process proc = rt.exec(comando);
			BufferedReader reader = new BufferedReader(new InputStreamReader(proc.getInputStream()));
			BufferedReader errorReader = new BufferedReader(new InputStreamReader(proc.getErrorStream()));
			String output = reader.readLine();
			if (output != null) {
				//Retorno no ambiente do mac
				if(output.contains("PID")) {
					output = reader.readLine();
					if (output != null) {
						String[] dados = output.split(" ");
						pid = dados[4];
					}
				}
				//Retorno no ambiente windows
				else {
					int pid_posicao = output.lastIndexOf(" ");
					pid = output.substring(pid_posicao, output.length());
				}

			}
			else {
				TestBase.logReport(Status.INFO, "Nenhum processo encontrado na porta: " + porta + ". Mensagem retornada: " +errorReader.readLine());
			}
		} catch (IOException erro) {
			TestBase.logReport(Status.FAIL,
					"Falha ao tentar localizar o PID do processa da porta: " + porta + ". Erro: " + erro);
		}
		return pid;
	}
	/**
	 * Retorna o PID do processo de acordo com a porta utilizada
	 * 
	 * @param porta do processo a ser buscado o PID
	 * @return pid
	 * @throws IOException
	 */
	public static String retornaProcessoPID2(String porta) {
		String pid = "";
		try {
			Runtime rt = Runtime.getRuntime();
			Process proc;
			proc = rt.exec("cmd /c netstat -ano | findstr " + porta);
			BufferedReader reader = new BufferedReader(new InputStreamReader(proc.getInputStream()));
			String output = reader.readLine();
			if (output != null) {
				int pid_posicao = output.lastIndexOf(" ");
				pid = output.substring(pid_posicao, output.length());
			}
		} catch (IOException erro) {
			TestBase.logReport(Status.FAIL,
					"Falha ao tentar localizar o PID do processa da porta: " + porta + ". Erro: " + erro);
		}
		return pid;
	}

	public static void finalizarProcessoPeloPID(String pid) {
		try {
			String OS = System.getProperty("os.name");
			String comando = "";
			Runtime rt = Runtime.getRuntime();
			if (OS.contains("Mac")) {
				comando = "kill -9 "+ pid;
			}
			else {
				comando = "cmd /c Taskkill /PID" + pid + " /T /F";
			}

			Process proc = rt.exec(comando);
			BufferedReader reader = new BufferedReader(new InputStreamReader(proc.getInputStream()));
			BufferedReader errorReader = new BufferedReader(new InputStreamReader(proc.getErrorStream()));
			String output = reader.readLine();
		} catch (IOException erro) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Falha ao tentar finalizar o processo de PID: " + pid + ". Erro: " + erro);
		}
	}

}
