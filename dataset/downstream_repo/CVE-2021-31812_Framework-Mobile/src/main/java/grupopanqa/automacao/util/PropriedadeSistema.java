package grupopanqa.automacao.util;

import java.io.File;

public class PropriedadeSistema {

	public static void definirCaCerts(String localCacerts) {
			File arquivoCacerts = new File(localCacerts);
			System.setProperty("javax.net.ssl.trustStore", arquivoCacerts.getAbsolutePath());
	}

}
