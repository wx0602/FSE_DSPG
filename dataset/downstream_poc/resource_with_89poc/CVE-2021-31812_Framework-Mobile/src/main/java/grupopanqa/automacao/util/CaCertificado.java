package grupopanqa.automacao.util;

import grupopanqa.automacao.util.EnumFramework.Status;

import javax.net.ssl.*;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.URL;
import java.security.KeyStore;
import java.security.cert.Certificate;
import java.security.cert.CertificateExpiredException;
import java.security.cert.X509Certificate;
import java.time.Instant;


/**
 * Classe responsavel em gerenciar validacao e insercao de novos CA Certs no arquivo keystore
 * @author 800041563
 *
 */
public class CaCertificado {

	/**
	 * Metodo responsavel por confiar temporariamente em todos os sites (CA Certs)
	 */
	private static void confiarTodosCertificado() {
		try {
		TrustManager[] confiarTodosCaCerts = new TrustManager[] { new X509TrustManager() {
			public java.security.cert.X509Certificate[] getAcceptedIssuers() {
				return null;
			}

			public void checkClientTrusted(X509Certificate[] certs, String authType) {
			}

			public void checkServerTrusted(X509Certificate[] certs, String authType) {
			}

		} };

		SSLContext ssl = SSLContext.getInstance("SSL");
		ssl.init(null, confiarTodosCaCerts, new java.security.SecureRandom());
		HttpsURLConnection.setDefaultSSLSocketFactory(ssl.getSocketFactory());

		// Implementacao do metodo que faz a validacao do host, retornando sempre true
		HostnameVerifier certificadoByPass = new HostnameVerifier() {
			public boolean verify(String hostname, SSLSession session) {
				return true;
			}
		};
		//Inserindo o metodo que realzia o by pass da validacao dos hosts 
		HttpsURLConnection.setDefaultHostnameVerifier(certificadoByPass);
		/* End of the fix */
		}
		catch(Exception erro) {
			TestBase.logReport(Status.FAIL, "Erro ao realizar procedimento para confiar em todos os certificados. Erro: " +erro);
		}
	}
	
	private static Certificate[] capturaCertificados(String url) {
		Certificate[] certs = null;
		try {
		URL destinationURL = new URL(url);
		HttpsURLConnection conn = (HttpsURLConnection) destinationURL.openConnection();
		conn.connect();
		certs = conn.getServerCertificates();
		}
		catch(Exception erro) {
			TestBase.logReport(Status.FAIL, "Erro ao tentar capturar os certificados da url: " + url + ". Erro: " +erro);
		}
		return certs;
		
	}
	
	private static void adicionaCertificadoCA(Certificate[] certs, String localCacert, String senhaCacert) {
		try {
			//Cria a instancia keyStore e carrega todos os dados existentes do CaCert existente
			KeyStore keyStore = KeyStore.getInstance(KeyStore.getDefaultType());
			File keystoreFile = new File(localCacert);
			FileInputStream fis = new FileInputStream(keystoreFile);
			keyStore.load(fis, senhaCacert.toCharArray());
			fis.close();
			
			//Adiciona cada certificado na instancia temporaria keyStore
			for (Certificate cert : certs) {
				if (cert instanceof X509Certificate) {
					try {
						((X509Certificate) cert).checkValidity();
						String certificadoAlias = "certificado" + Long.toString(Instant.now().toEpochMilli()); 
						keyStore.setCertificateEntry(certificadoAlias, cert);
						TestBase.logReport(Status.INFO, "Adicionado certificado: " + certificadoAlias + " na keyStore " + keystoreFile.getAbsolutePath());
					} catch (CertificateExpiredException erro) {
						TestBase.logReport(Status.INFO, "Não foi possível adicionar o certificado. Certificado expirado: " + cert.toString()+". Erro: " + erro);
					}
				} else {
					TestBase.logReport(Status.INFO, "Não foi possível adicionar o certificado. Tipo do certificado informado desconhecido: " + cert.toString());
				}
			}
			
			//Salva os dados da instância keyStore no cacert
			FileOutputStream out = new FileOutputStream(keystoreFile);
			keyStore.store(out, senhaCacert.toCharArray());
			out.close();
			
		}
		catch(Exception erro) {
			TestBase.logReport(Status.FAIL, "Erro ao tentar adicionar CA certificado na keystore. Erro: " + erro);
		}
		
	}
	
	public synchronized static void adicionaPermissao(String url, String localCacert, String senhaCacert ){
		confiarTodosCertificado();
		Certificate[] certificados = capturaCertificados(url);
		adicionaCertificadoCA(certificados, localCacert, senhaCacert);
	}

}
