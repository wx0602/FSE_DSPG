package grupopanqa.automacao.util;

/**
 * Enum que auxiliam na automacao
 * @author 800041563
 *
 */
public class EnumFramework{
	
	public enum DEVICE{
		fisico,
		emulador,
		browserstack
	}
	
	public enum Navegadores{
		Chrome,
		ChromeHeadLess,
		IE,
		Firefox
	}
	public enum Ambiente{
		DEV,
		QA,
		HOM,
		PROD
	}
	public enum Sistema{
		chatbot
	}
	public enum Status{
		DEBUG,
		ERROR,
		FAIL,
		FATAL,
		INFO,
		PASS,
		SKIP,
		WARNING
	}
	public enum Propriedade{
		Id,
		Name,
		ClassName,
		Css,
		How,
		LinkText,
		PartialLinkText,
		TagName,
		Using,
		Xpath
	}
	
	public enum AtributoMobile{
		Id,
		Name,
		ClassName,
		CssSelector,
		LinkText,
		PartialLinkText,
		TagName,
		Xpath,
		Predicate,
		AccessibilityId
		
	}
	
	public enum AtributoWeb{
		Id,
		Name,
		ClassName,
		CssSelector,
		LinkText,
		PartialLinkText,
		TagName,
		Xpath
	}
	
	public enum ApiTipoBody{
		Json,
		Properties
	}
	
	public enum BancoDados{
		SQLServer
	}
	
	public enum Direcao{
		PARA_CIMA,
		PARA_BAIXO,
		PARA_DIREITA,
		PARA_ESQUERDA
	}
	public enum Velocidade{
		RAPIDO,
		NORMAL,
		DEVAGAR
	}
	
}


	
