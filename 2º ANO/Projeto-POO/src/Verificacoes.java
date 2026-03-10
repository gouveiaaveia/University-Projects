/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.Scanner;
import java.util.ArrayList;
import java.io.Serializable;

/**
 * Classe responsável por validar diferentes tipos de entradas fornecidas pelo usuário.
 */
public class Verificacoes implements Serializable{

    /**
     * Valida a entrada do usuário para as opções "s" (sim) ou "n" (não).
     *
     * @param sc Scanner para leitura da entrada do usuário.
     * @return o caractere 's' para sim ou 'n' para não.
     */
    public char verificaSimNao(Scanner sc) {
        char c = '\0';

        while (c != 's' && c != 'n') {
            System.out.print("Opção (s/n): ");
            String opcao = sc.nextLine().trim().toLowerCase();

            if (opcao.length() == 1 && (opcao.charAt(0) == 's' || opcao.charAt(0) == 'n')) {
                c = opcao.charAt(0);
            } else {
                System.out.println("Entrada inválida! Digite 's' ou 'n'.");
            }
        }

        return c;
    }

    /**
     * Valida e retorna um código de produto inserido pelo usuário.
     *
     * @param sc Scanner para leitura da entrada do usuário.
     * @return o código do produto como uma string válida.
     */
    public String verificaCodigo(Scanner sc){
        int codigo;
        String cod;
        do{
            System.out.print("Código do produto: ");
            cod= sc.nextLine();
            codigo = stringInteger(cod);
        }while(codigo == 0);

        return cod;
    }

    /**
     * Converte uma string em um número inteiro. Retorna 0 se a string não for válida.
     *
     * @param op a string a ser convertida.
     * @return o número inteiro correspondente ou 0 se inválido.
     */
    public int stringInteger(String op){
        int valor = 0;
        try{
            valor = Integer.parseInt(op);
            return valor;
        }catch (NumberFormatException e){
            System.out.println("Opção inválida!!");
            return 0;
        }
    }

    /**
     * Converte uma string em um número de ponto flutuante. Retorna 0.0 se a string não for válida.
     *
     * @param op a string a ser convertida.
     * @return o número double correspondente ou 0.0 se inválido.
     */
    public double stringDouble(String op){
        double valor = 0;
        try{
            valor = Double.parseDouble(op);
            return valor;
        }catch (NumberFormatException e){
            System.out.println("Opção inválida!!");
            return 0;
        }
    }

    /**
     * Converte uma string em uma opção de menu (inteiro). Retorna 0 se a string não for válida.
     *
     * @param op a string a ser convertida.
     * @return a opção como inteiro ou 0 se inválida.
     */
    public int opcaoMenu(String op){
        int opcao = 0;
        try{
            opcao = Integer.parseInt(op);
            return opcao;
        }catch (NumberFormatException e){
            return 0;
        }
    }

    /**
     * Verifica se um NIF é válido e está em um formato correto.
     *
     * @param nif o NIF a ser validado.
     * @param listaCliente a lista de clientes para verificar duplicação.
     * @return true se o NIF for válido; false caso contrário.
     */
    public boolean verificaNif(String nif, ArrayList<Cliente> listaCliente) {

        if (nif == null || nif.length() != 9) {
            System.out.println("Erro: O NIF deve ter 9 dígitos.");
            return false;
        }

        if (!nif.matches("^[0-9]+$")) {
            System.out.println("Erro: O NIF deve ter apenas números.");
            return false;
        }

        return true;
    }

    /**
     * Verifica se a localização inserida é válida (Madeira, Portugal Continental ou Açores).
     *
     * @param localizacao a localização a ser validada.
     * @return true se a localização for válida; false caso contrário.
     */
    public boolean verificaLocalizacao(String localizacao) {
        if (localizacao == null){
            System.out.println("Erro:Localização incorreta.");
            return false;
        }
        if(!localizacao.equalsIgnoreCase("madeira") && !localizacao.equalsIgnoreCase("portugal continental") && !localizacao.equalsIgnoreCase("açores")){
            System.out.println("Erro:Localização incorreta.");
            return false;
        }
        return true;
    }

    /**
     * Verifica se uma data está no formato correto e se é válida.
     *
     * @param data a data no formato "dd-mm-aaaa".
     * @return true se a data for válida; false caso contrário.
     */
    public boolean verificaData(String data) {
        // Verificar se a data é nula ou tem comprimento errado
        if (data == null) {
            System.out.println("Erro: Formato da data incorreto.");
            return false;
        }

        String[] valores = data.split("-");

        if (valores.length != 3) {
            System.out.println("Erro: Data não contém três partes.");
            return false;
        }

        if (!valores[0].matches("\\d{2}") || !valores[1].matches("\\d{2}") || !valores[2].matches("\\d{4}")) {
            System.out.println("Erro: Partes da data não estão no formato correto.");
            System.out.println("Dia: " + valores[0] + ", Mês: " + valores[1] + ", Ano: " + valores[2]);
            return false;
        }

        int dia, mes, ano;

        try {
            dia = Integer.parseInt(valores[0]);
            mes = Integer.parseInt(valores[1]);
            ano = Integer.parseInt(valores[2]);
        } catch (NumberFormatException e) {
            System.out.println("Erro: Conversão falhou.");
            return false;
        }

        if (mes < 1 || mes > 12) {
            System.out.println("Erro: Mês inválido.");
            return false;
        }

        if (ano < 1500) {
            System.out.println("Erro: Ano inválido.");
            return false;
        }

        int[] diasPorMes = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        if (mes == 2 && anoBissexto(ano)) {
            diasPorMes[1] = 29;
        }

        if (dia < 1 || dia > diasPorMes[mes - 1]) {
            System.out.println("Erro: Dia inválido.");
            return false;
        }

        return true;
    }

    private boolean anoBissexto(int ano) {
        return (ano % 4 == 0 && ano % 100 != 0) || (ano % 400 == 0);
    }



    /**
     * Verifica se uma categoria é válida.
     * As categorias aceitas são: "Beleza", "BemEstar", "Bebes", "Animais" e "Outros".
     *
     * @param categoria a categoria a ser validada.
     * @return true se a categoria for válida; false caso contrário.
     */
    public boolean verificaCategoria(String categoria){
        if(!categoria.equalsIgnoreCase("Beleza") && !categoria.equalsIgnoreCase("BemEstar") && !categoria.equalsIgnoreCase("Bebes") && !categoria.equalsIgnoreCase("Animais") && !categoria.equalsIgnoreCase("Outros")){
            System.out.println("Erro: Categoria incorreta.");
            return false;
        }
        return true;
    }

    /**
     * Verifica se uma string atende aos critérios especificados (não é nula, não contém apenas números e possui tamanho maior que o especificado).
     *
     * @param palavra a string a ser validada.
     * @param tamanho o tamanho mínimo permitido.
     * @return true se a string for válida; false caso contrário.
     */
    public boolean verificaString(String palavra, int tamanho) {
        if (palavra==null || palavra.matches("^[0-9]+$") || palavra.length()<=tamanho){
            System.out.println("Erro.");
            return false;
        }
        return true;
    }
}

