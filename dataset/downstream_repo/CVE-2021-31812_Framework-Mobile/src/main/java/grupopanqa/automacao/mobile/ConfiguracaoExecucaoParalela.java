package grupopanqa.automacao.mobile;

import org.junit.platform.engine.ConfigurationParameters;
import org.junit.platform.engine.support.hierarchical.ParallelExecutionConfiguration;
import org.junit.platform.engine.support.hierarchical.ParallelExecutionConfigurationStrategy;

/**
 * Classe responsável por implementar ParallelExecutionConfigurationStrategy
 * Strategy custom para pegar setar a quantidade de devices conectados com a quantidade de threads
 * para execução em paralelo
 * @author 42289911810
 *
 */
public class ConfiguracaoExecucaoParalela implements ParallelExecutionConfigurationStrategy{

	private int qtdDevicesConectados;
	
	/*
	 * Construtor - Armazena a quantidade de devices conectados no computador
	 */
	public ConfiguracaoExecucaoParalela() {
            qtdDevicesConectados = Device.listarDevicesConectados().size();
            if (qtdDevicesConectados == 0) {
                //Necessário validação para que, mesmo que não haja device conectado, seja possível rodar com
                //apenas uma thread (sem paralelismo)
                qtdDevicesConectados++;
            }
            System.out.println("Quantidade de devices conectados: " + qtdDevicesConectados);
	}
	
	/**
	 * Override criado uma nova configuração
	 */
	@Override
	public ParallelExecutionConfiguration createConfiguration(ConfigurationParameters configurationParameters) {
		return new ParallelExecutionConfiguration() {
			
            @Override
            public int getParallelism() {
                return qtdDevicesConectados;
            }

            @Override
            public int getMinimumRunnable() {
                return 1;
            }

            @Override
            public int getMaxPoolSize() {
                return qtdDevicesConectados;
            }

            @Override
            public int getCorePoolSize() {
                return qtdDevicesConectados;
            }

            @Override
            public int getKeepAliveSeconds() {
                return 30;
            }
		};
	}

}
