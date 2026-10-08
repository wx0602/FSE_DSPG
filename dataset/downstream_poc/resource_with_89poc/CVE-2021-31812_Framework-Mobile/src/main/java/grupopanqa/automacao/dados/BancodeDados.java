package grupopanqa.automacao.dados;

import grupopanqa.automacao.util.EnumFramework.BancoDados;
import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.TestBase;
import grupopanqa.automacao.util.entidade.BDConexao;
import org.junit.jupiter.api.Test;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class BancodeDados {

	private Connection conexao;

	@Test
	public void testeConexao() {

		BDConexao conexao = new BDConexao(BancoDados.SQLServer, "PANFDBH3091", "MONITORPANVEIC_QA", "1433", "", "");
		conectar(conexao);
		List<?> teste = realizarConsulta("select TOP 20 * from dbo.CLOGPLUG");
		fecharConexao();
		for (int cont = 0; cont < teste.size(); cont++) {
			System.out.println(teste.get(cont));
		}

	}

	/**
	 * Metodo responsavel por realizar a consulta (select) no banco de dados
	 * 
	 * @param select String com o select a ser utilizado (ex: 'select TOP 20 * from
	 *               dbo.TRETCAMPO')
	 * @return List<List<String>> Lista de lista de registros. A primeira lista de
	 *         registros é o header (cabecalho)
	 */
	public List<List<String>> realizarConsulta(String select) {
		List<String> selectHeader = new ArrayList<String>();
		List<List<String>> listaRegistros = new ArrayList<List<String>>();
		try {
			Statement stmt = conexao.createStatement();
			ResultSet rs = stmt.executeQuery(select);
			ResultSetMetaData rsmd = rs.getMetaData();

			int qtdColunas = rsmd.getColumnCount();

			for (int cont = 1; cont <= qtdColunas; cont++) {
				selectHeader.add(rsmd.getColumnLabel(cont));
			}
			listaRegistros.add(selectHeader);
			while (rs.next()) {
				List<String> selectRegistro = new ArrayList<String>();
				for (int cont = 1; cont <= qtdColunas; cont++) {
					selectRegistro.add(rs.getString(cont));
				}
				listaRegistros.add(selectRegistro);
			}
			stmt.close();
			rs.close();
		} catch (SQLException e) {
			// // Erro caso haja problemas para se conectar ao banco de dados
			e.printStackTrace();
		}

		return listaRegistros;
	}

	/**
	 * Realiza a conexao com o banco de dados
	 * 
	 * @param dadosConexao BDConexao com os dados da conexao. Caso o atributo porta
	 *                     esteja vazio, sera utilizado o padrao. Caso o atributo
	 *                     usuario esteja vazio, sera realizada a conexao com
	 *                     autenticacao do windows
	 * 
	 */
	public void conectar(BDConexao dadosConexao) {
		String conexaoSGBD = "";
		String portaPadrao = "";
		String driverConexao = "";

		// Verifica qual SGBD sera realizada a conexao
		switch (dadosConexao.getSgbd()) {
		case SQLServer:
			conexaoSGBD = "sqlserver";
			portaPadrao = "1433";
			driverConexao = "com.microsoft.sqlserver.jdbc.SQLServerDriver";

		}

		String servidor = dadosConexao.getServidor();
		String bancoDeDados = dadosConexao.getBancoDeDados();
		String usuario = dadosConexao.getUsuario();
		String senha = dadosConexao.getSenha();
		String porta = dadosConexao.getPorta();
		if (porta == "") {
			porta = portaPadrao;
		}

		String stringConexao = "";

		// Caso o usuario seja vazio, sera realizada a conexao com autenticacao do
		// windows
		if (usuario == "") {
			stringConexao = "jdbc:" + conexaoSGBD + "://" + servidor + ":" + porta + ";databaseName=" + bancoDeDados
					+ ";integratedSecurity=true";
		} else {
			stringConexao = "jdbc:" + conexaoSGBD + "://" + servidor + ":" + porta + ";databaseName=" + bancoDeDados
					+ ";user=" + usuario + ";password=" + senha + ";";
		}

		try {
			Class.forName(driverConexao);
			conexao = DriverManager.getConnection(stringConexao);

		} catch (ClassNotFoundException e) {
			// // Erro caso o driver JDBC não foi instalado
			TestBase.logReport(Status.FAIL, "Erro em relacao ao driver JDBC. Descricao: " + e);
		} catch (SQLException e) {
			// // Erro caso haja problemas para se conectar ao banco de dados
			TestBase.logReport(Status.FAIL, "Erro ao realizar conexao com o banco de dados. Descricao: " + e);
		}
	}

	/**
	 * Fecha a conexao com o banco de dados
	 */
	public void fecharConexao() {
		try {
			conexao.close();
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			TestBase.logReport(Status.FAIL, "Erro ao finalizar conexao com o banco de dados. Descricao: " + e);
		}
	}

}
