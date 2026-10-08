package grupopanqa.automacao.util;

import static grupopanqa.automacao.dados.ConfiguracaoDados.getReportPath;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.TimeZone;

import org.junit.Test;
import org.zeroturnaround.zip.ZipUtil;

import grupopanqa.automacao.dados.ConfiguracaoDados;
import grupopanqa.automacao.mobile.Device;

public class Util {
	
	static ConfiguracaoDados configFile;
	
	private static String pathReport = null;
	private static String pathReportCompleto = null;
	public static Device device;
	
	
	
	public static void apagaReportAntesExecucao() {

		setPathReportCompleto(System.getProperty("user.dir") + File.separator + getReportPath());

		File pathDefault_ = new File(getPathReportCompleto());

		if (!pathDefault_.exists())
			pathDefault_.mkdir();

		try {
			File dir = null;
			dir = new File(getPathReportCompleto());
			File[] listFiles = dir.listFiles();

			if (listFiles != null) {

				for (File file : listFiles) {
					if (file.getName().contains(".jpeg") == false) {
						System.out.println("The file not be deleted " + file.getName());
					} else {
						System.out.println("Deleting " + file.getName());
						file.delete();
					}
				}
			}

			System.out.println("Files deleted successfully");
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	@Test
	public static void zipReportFiles() {
		
		if (ConfiguracaoDados.recuperarValor("BACKUP_REPORTS").equals("true")) {
		String pathReportBackup = null;			

			SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd_HHmmss");
			dateFormat.setTimeZone(TimeZone.getTimeZone("GMT-3:00"));
			String data = dateFormat.format(new Date(System.currentTimeMillis()));
			
			pathReportBackup = System.getProperty("user.dir") + File.separator + "target" + File.separator +  "reports-backup";

//			File log4j = new File(System.getProperty("user.dir") + File.separator + "target" + File.separator + "log");

//			try {
//				FileSystemUtils.copyRecursively(log4j, new File(pathReport));
//			} catch (IOException e1) {
//				e1.printStackTrace();
//			}

			File path = new File(pathReportBackup);
			String pathReportZip = pathReportBackup + File.separator + "Report_" + data + ".zip";

			if (!path.exists())
				path.mkdir();

			try {
				ZipUtil.pack(new File(System.getProperty("user.dir") + File.separator + ConfiguracaoDados.getReportPath()), new File(pathReportZip));
				System.out.println("Backup of Report saved on path: " + pathReportZip);
			} catch (Exception e) {
				System.out.println("Cannot zip a folder to Report");
				e.printStackTrace();
			}
		}
	}
	
	public static String getPathReport() {
		return pathReport;
	}

	public static void setPathReport(String pathReport) {
		Util.pathReport = pathReport;
	}

	public static String getPathReportCompleto() {
		return pathReportCompleto;
	}

	public static void setPathReportCompleto(String pathReportCompleto) {
		Util.pathReportCompleto = pathReportCompleto;
	}
	
}
