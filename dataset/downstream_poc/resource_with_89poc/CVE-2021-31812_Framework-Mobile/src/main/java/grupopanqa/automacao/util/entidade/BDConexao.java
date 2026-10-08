package grupopanqa.automacao.util.entidade;

import grupopanqa.automacao.util.EnumFramework.BancoDados;

/**
 * Classe responsavel por armazenar os dados de conexao com o banco de dados
 * @author 800041563
 *
 */
public class BDConexao {
	private BancoDados sgbd;
	private String servidor;
	private String bancoDeDados;
	private String porta;
	private String usuario;
	private String senha;

	/**
	 * Construtor para objeto de armazenamento de dados de conexao (para montrar string de conexao)
	 * @param sgbd - Enum do tipo de SGBD a ser realizada a conexao
	 * @param servidor - Nome do servidor
	 * @param bancoDeDados - Nome do banco de dados
	 * @param porta - Porta do banco (deixar em branco sera utilizada a porta padrao)
	 * @param usuario - Usuario para conexao (deixar embranco sera realizada a conexao com autenticacao do windows)
	 * @param senha - Senha para conexao (caso seja utilizada autenticacao do windows, valor da variavel senha sera desconsiderada)
	 */
	public BDConexao(BancoDados sgbd, String servidor, String bancoDeDados, String porta, String usuario,String senha) {
		setSgbd(sgbd);
		setServidor(servidor);
		setBancoDeDados(bancoDeDados);
		setPorta(porta);
		setUsuario(usuario);
		setSenha(senha);
	}
	
	public BancoDados getSgbd() {
		return sgbd;
	}

	public void setSgbd(BancoDados sgbd) {
		this.sgbd = sgbd;
	}

	public String getServidor() {
		return servidor;
	}

	public void setServidor(String servidor) {
		this.servidor = servidor;
	}

	public String getBancoDeDados() {
		return bancoDeDados;
	}

	public void setBancoDeDados(String bancoDeDados) {
		this.bancoDeDados = bancoDeDados;
	}

	public String getPorta() {
		return porta;
	}

	public void setPorta(String porta) {
		this.porta = porta;
	}

	public String getUsuario() {
		return usuario;
	}

	public void setUsuario(String usuario) {
		this.usuario = usuario;
	}

	public String getSenha() {
		return senha;
	}

	public void setSenha(String senha) {
		this.senha = senha;
	}

}
