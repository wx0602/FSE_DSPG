package grupopanqa.automacao.mobile;

import grupopanqa.automacao.util.EnumFramework.Status;
import grupopanqa.automacao.util.TestBase;
import org.json.JSONArray;
import org.json.JSONObject;
import org.openqa.selenium.remote.DesiredCapabilities;

import java.io.File;
import java.util.*;

/**
 * Realiza a gestão (reserva e liberação) dos devices (capabilites) para uso
 * 
 * @author 800041563
 *
 */
public class ControleDeviceCapabilities {

	private static JSONArray devices = null;
	private static List<DesiredCapabilities> listaDevicesDisponiveis = new ArrayList<>();
	private static List<DesiredCapabilities> listaDevicesOcupados = new ArrayList<>();
	private static Map<String, DesiredCapabilities> listaCapabilityPorThread = new HashMap<String, DesiredCapabilities>();

	/**
	 * Disponibiliza os capabilities para uso e remove da lsita de reservados
	 * 
	 * @param capabilities
	 */
	public static void liberaDevice(DesiredCapabilities capabilities) {
		listaDevicesDisponiveis.add(capabilities);
		listaDevicesOcupados.remove(capabilities);
	}

	/**
	 * Reserva os capabilities (insere na lista de ocupados e na lista de
	 * capabilities por thread) e remove da lista de disponiveis
	 * 
	 * @param capabilities
	 */
	private static void reservaDevice(DesiredCapabilities capabilities) {
		listaDevicesDisponiveis.remove(capabilities);
		listaDevicesOcupados.add(capabilities);
		listaCapabilityPorThread.put(String.valueOf(Thread.currentThread().getId()), capabilities);
	}

	/**
	 * Retorna device (capabilities) que esteja disponível para utilização
	 * (realizando a sua reserva) Método executa as solicitações de forma síncrona,
	 * para evitar problemas de acesso paralelo à lista de devices
	 * 
	 * @param posicao Posição do device da lista. Por padrão informar 0 para receber
	 *                o primeiro device disponível
	 * @return DesiredCapabilities capabilities disponível
	 */
	public synchronized static DesiredCapabilities getDeviceDisponivel(int posicao) {
		DesiredCapabilities capabilities = null;
		try {
			// Caso a lista de devices disponivel seja 0, é realizado a disponibilização do
			// device que estava preso ao mesmo id da thread
			if (listaDevicesDisponiveis.size() == 0) {
				liberaDevice(listaCapabilityPorThread.get(String.valueOf(Thread.currentThread().getId())));
			}
			capabilities = listaDevicesDisponiveis.get(posicao);
			reservaDevice(capabilities);
		} catch (Exception erro) {
			TestBase.logReport(Status.FAIL,
					"Erro ao tentar vincular um device (capabilities) para o teste. Erro; " + erro);
		}
		return capabilities;
	}

	/**
	 * Monta a lsita de capabilites por device, de acordo com o arquivo de
	 * configuração (device.json)
	 * 
	 * @param devicesCapabilities Capabilities do tipo de device do arquivo
	 *                            device.json
	 */
	public static void montaListaDeviceCapabilities(JSONObject devicesCapabilities) {
		// Primeiro, monta a lista de capabilities que será genérico a todos os devices
		DesiredCapabilities dcGenerico = new DesiredCapabilities();
		Iterator<String> categoriaDeviceChaves = devicesCapabilities.keys();
		while (categoriaDeviceChaves.hasNext()) {
			String chave_generico = categoriaDeviceChaves.next();
			if (chave_generico.equals("devices")) {
				devices = devicesCapabilities.getJSONArray(chave_generico);
			} else if (chave_generico.equals("app")) {
				Object valor = devicesCapabilities.get(chave_generico);
				if (valor.toString().contains("resources")) {
					File fileRelative = new File(valor.toString());
					dcGenerico.setCapability(chave_generico, fileRelative.getAbsolutePath());
				} else {
					dcGenerico.setCapability(chave_generico, valor);
				}
			} else {
				Object valor = devicesCapabilities.get(chave_generico);
				dcGenerico.setCapability(chave_generico, valor);
			}
		}

		// Segundo, monta a lista de capabilities que são exclusivos para cada device
		if (devices == null) {
			// devices == null significa que é um real device ou emulador.
			//Real Devices e Emuladores nao é necessario informar o id, pois é capturado automaticamente
			//No device jsondevice nao há o jsonObject devices, ao contrário de devices na nuvem
			List<String> listaDevicesIds = Device.listarDevicesConectados();
			if (listaDevicesIds.size() == 0) {
				TestBaseMobile.logReport(Status.WARNING, "Não foi encontrado nenhum device conectado na máquina executora");
			}else {
				listaDevicesIds.forEach(item -> {
					DesiredCapabilities dc = new DesiredCapabilities();
					dc.setCapability("udid", item);
					dc.setCapability("deviceName", item);
					listaDevicesDisponiveis.add(dc.merge(dcGenerico));
				});
			}

		} else {
			//Quando a execução é em devices na nuvem (onde é necessário cadastrar o jsonObject device para cada device
			devices.forEach(item -> {
				JSONObject device = (JSONObject) item;
				DesiredCapabilities dc = new DesiredCapabilities();
				Iterator<String> device_chaves = device.keys();
				while (device_chaves.hasNext()) {
					String chave = device_chaves.next();
					Object valor = device.get(chave);
					dc.setCapability(chave, valor);
				}
				// Terceiro, realiza o merge de device dos seus capabilities exclusivos com os
				// capabilities genéricos e adiciona na lista
				listaDevicesDisponiveis.add(dc.merge(dcGenerico));
			});
		}

	}



}
