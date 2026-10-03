package grupopanqa.automacao.util;

import grupopanqa.automacao.mobile.TestBaseMobile;
import org.apache.poi.EncryptedDocumentException;
import org.apache.poi.openxml4j.exceptions.InvalidFormatException;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Iterator;

/**
 * Classe com os metodos relacionados a criação, leitura e alteração de planilha excel
 * @author 800041563
 *
 */
public class Excel {

	Workbook workbook;
	Sheet sheet;
	Row row;
	Cell cell;
	
	/**
	 * Realiza o carregamento da planilha excel
	 * @param caminhoArquivo Caminho completo do arquivo excel
	 * @throws EncryptedDocumentException
	 * @throws InvalidFormatException
	 * @throws IOException
	 */
	public void carregarArquivo(String caminhoArquivo) throws EncryptedDocumentException, InvalidFormatException, IOException{
		workbook = WorkbookFactory.create(new FileInputStream(new File(caminhoArquivo)));
	}

	/**
	 * Cria um novo arquivo excel
	 * @param caminhoArquivo Caminho completo do arquivo excel a ser criado
	 * @throws EncryptedDocumentException
	 * @throws InvalidFormatException
	 * @throws IOException
	 */
	public void criarArquivo(String caminhoArquivo) throws EncryptedDocumentException, InvalidFormatException, IOException{
		FileOutputStream output = new FileOutputStream(caminhoArquivo);
		workbook = new XSSFWorkbook();
		workbook.write(output);
	}	
	
	/**
	 * Criar nova planilha no arquivo excel
	 * @param nomePlanilha Nome da planilha a ser criada
	 */
	public void criarPlanilha(String nomePlanilha){
		workbook.createSheet(nomePlanilha);
	}
	
	/**
	 * Salvar as alterações realizadas no arquivo excel
	 * @param nomeExcel Nome do arquivo a ser salvo
	 */
	public void salvarArquivoExcel(String nomeExcel){
		FileOutputStream output_file = null;
		try {
			output_file = new FileOutputStream(new File(nomeExcel));
			workbook.write(output_file);
		} catch (IOException e) {
			e.printStackTrace();
		}
		
	}
	
	/**
	 * Seleciona a planilha desejada pelo nome
	 * @param nome Nome da planilha
	 */
	public void recuperarPlanilha(String nome){
		sheet = workbook.getSheet(nome);
	}
	
	/**
	 * Seleciona a planilha desejada pelo numero dela (index)
	 * @param numero Index da planilha (começando pelo zero)
	 */
	public void recuperarPlanilha(int numero){
		sheet = workbook.getSheetAt(numero);
	}
	
	/**
	 * Seleciona a linha desejada pelo numero dela
	 * @param numero Numero da linha a ser selecionada
	 */
	public void recuperarLinha(int numero){
		if (sheet.getRow(numero) == null){
			row = sheet.createRow(numero);
		}
		else{
			row = sheet.getRow(numero);
		}
	}
	
	/**
	 * Seleciona a celula desejada pelo numero dela
	 * @param numero Numero da linha a ser selecionada
	 */
	public void recuperarCelula(int numero){
		if (row.getCell(numero) == null){
			cell = row.createCell(numero);
		}
		else{
			cell = row.getCell(numero);
		}
	}
	
	/**
	 * Avanca para a proxima linha da planilha
	 */
	public void avancarLinha(){
		row = sheet.getRow(row.getRowNum()+1);
		cell = row.getCell(cell.getColumnIndex());
	}
	
	/**
	 * Adiciona linha na planilha na ultima posicao
	 */
	public void adicionarUltimaLinha(){
		row = sheet.createRow(sheet.getLastRowNum()+1);
		if (cell == null){
			cell = row.getCell(0);
		}
		else{
			cell = row.getCell(cell.getColumnIndex());
		}
		
	}	
	
	/**
	 * Recupera o texto da celula
	 * @return Texto da celula
	 */
	public String recuperarTextoCelula(){
		return cell.getStringCellValue();
	}
	
	/**
	 * Adiciona o texto na celula
	 * @param texto Texto a ser selecionado
	 */
	public void adicionarTextoCelula(String texto){
		cell.setCellValue(texto);
	}
	
	/**
	 * Adicionar texto na celula da coluna desejada
	 * @param texto Texto a ser adicionado
	 * @param nomeColuna Coluna a ser buscada
	 */
	public void adicionarTextoCelulaPelaColuna(String texto, String nomeColuna){
		int numColuna = recuperarHeaderIndex(nomeColuna);
		recuperarCelula(numColuna);
		adicionarTextoCelula(texto);
	}
	
	/**
	 * Adicionar texto na celula da coluna desejada
	 * @param int Index da coluna
	 * @param nomeColuna Coluna a ser buscada
	 */
	public void adicionarTextoCelulaPelaColuna(String texto, int index){
		recuperarCelula(index);
		adicionarTextoCelula(texto);
	}
	
	/**
	 * Verifica o nome do Header do numero da coluna informado por parametro
	 * @param numColuna Numero da coluna a verificar o nome do header
	 * @return Nome do header
	 */
	public String recuperarHeaderNome(int numColuna){
		return sheet.getRow(0).getCell(numColuna).getStringCellValue();
	}

	/**
	 * Verifica se existe registro na proxima linha
	 * @return True - Existe próxima linha / False - Não existe registro na proxima linha
	 */
	public Boolean verificaExisteCelulaProximaLinha(){
		Row nextRow = sheet.getRow(row.getRowNum() + 1);
		if (nextRow == null || nextRow.getCell(cell.getColumnIndex()).getCellTypeEnum() == CellType.BLANK){
		    return false;
		}
		else{
			return true;
		}
	}	
	
	/**
	 * Recuperar o index através do nome do Header
	 * @param nome Nome da planilha que se deseja descobrir o index
	 * @return Index do Header. Retorna -1 caso não exista o Header informado
	 */
	public int recuperarHeaderIndex(String nome){
		Iterator<Cell> cellIterator = sheet.getRow(0).cellIterator();
		while (cellIterator.hasNext()){
			Cell cell = cellIterator.next();
			if (cell.getStringCellValue().equals(nome)){
				return cell.getColumnIndex();
			}
		}
		return -1;
	}
	
	/**
	 * Criar novo header
	 * @param nomeHeader Nome do header a ser criado
	 * @return Index do novo header criado
	 */
	public int adicionarHeader(String nomeHeader){
		if (sheet.getRow(0) == null){
			sheet.createRow(0);//.createCell(0);
		}
		int indexNovoHeader = sheet.getRow(0).getLastCellNum();
		if (indexNovoHeader == -1) indexNovoHeader = 0;
		sheet.getRow(0).createCell(indexNovoHeader).setCellValue(nomeHeader);
		
		return indexNovoHeader;
	}
	
	/**
	 * Metodo para percorrer linhas
	 * @param numColuna Numero da coluna a numLinha n�mero da linha
	 * @return retorna valor da celula
	 */
	public String percorrerLinhas(int numColuna, int numLinha){	
		String valor = null;
		try {
			valor = sheet.getRow(numLinha).getCell(numColuna).getStringCellValue();
		}catch(Exception ex) {
			TestBaseMobile.logReport(grupopanqa.automacao.util.EnumFramework.Status.ERROR, "boleto nao identificado na planilha");		
		}
		return valor;
		
	}
	
	/**
	 * Adiciona o texto na celula
	 * @param texto Texto a ser selecionado
	 */
	public String preencherCelula(int numColuna,int numLinha, String code, String textoRetorno){
		//if (texto != null) {
		try {
		if(code == "500") {
			if (sheet.getRow(numLinha).getCell(numColuna) == null){
				sheet.getRow(numLinha).createCell(numColuna);
			}
			
		sheet.getRow(numLinha).getCell(numColuna).setCellValue(textoRetorno);
		return "Boleto não identificado";
		}
		else
		{
			if (sheet.getRow(numLinha).getCell(numColuna) == null){
				sheet.getRow(numLinha).createCell(numColuna);
			}
			sheet.getRow(numLinha).getCell(numColuna).setCellValue("boleto pode ser Pago");
			String boleto;
			boleto = sheet.getRow(numLinha).getCell(1).toString();
			return boleto;
		}
		}catch(Exception ex) {
			TestBaseMobile.logReport(grupopanqa.automacao.util.EnumFramework.Status.ERROR, "Nao ha este tipo de boleto nesta planilha");
		}
		return textoRetorno;
		
		
		//sheet.getRow(numLinha).getCell(numColuna).getStringCellValue();
		//cell.setCellValue(texto);
	}
}
