/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.ArrayList;
import java.util.Scanner;
import java.io.Serializable;

/**
 * Classe que representa um cliente com informações como nome, NIF e localização.
 */
public class Cliente implements Serializable{

    private String nome;
    private String nif;
    private String localizacao;

    /**
     * Construtor que inicializa um cliente com os dados fornecidos.
     *
     * @param nome o nome do cliente.
     * @param nif o número de identificação fiscal (NIF) do cliente.
     * @param localizacao a localização do cliente.
     */
    public Cliente(String nome, String nif, String localizacao){
        this.nome = nome;
        this.nif = nif;
        this.localizacao =localizacao;
    }

    /**
     * Construtor padrão que inicializa um cliente com valores vazios.
     */
    public Cliente(){
        this.nome = "";
        this.nif = "";
        this.localizacao = "";
    }

    /**
     * Cria um cliente a partir das entradas do usuário.
     *
     * @param listaCliente a lista de clientes existentes para verificar duplicidades de NIF.
     * @param sc o objeto Scanner para leitura da entrada do usuário.
     * @param v o objeto Verificacoes para validação das entradas.
     */
    public void criarCliente(ArrayList<Cliente> listaCliente, Scanner sc, Verificacoes v){
        String nome;
        do {
            System.out.print("Nome: ");
            nome = sc.nextLine();
        } while (!v.verificaString(nome,2));
        setNome(nome);

        String nif;
        boolean encontrado;
        do {
            encontrado = false;
            System.out.print("NIF: ");
            nif = sc.nextLine();
            for (Cliente cliente : listaCliente) {
                if (nif.equals(cliente.getNif())) {
                    System.out.println("Erro: Este NIF não está disponível.");
                    encontrado = true;
                }
            }
        } while (!v.verificaNif(nif, listaCliente) || encontrado);
        setNif(nif);

        String localizacao;
        do {
            System.out.print("Localização (Madeira,Açores,Portugal Continental): ");
            localizacao = sc.nextLine();
        } while (!v.verificaLocalizacao(localizacao));
        setLocalizacao(localizacao.toLowerCase()); //vai em minusculos por causa do que temmos na tebela
    }


    /**
     * Edita as informações de um cliente existente.
     *
     * @param listaCliente a lista de clientes existentes para verificar duplicidades de NIF.
     * @param sc o objeto Scanner para leitura da entrada do usuário.
     * @param v o objeto Verificacoes para validação das entradas.
     */
    public void EditaCliente(ArrayList<Cliente> listaCliente, Scanner sc, Verificacoes v){
        System.out.print("\nEditar nome? ");
        char resposta = v.verificaSimNao(sc);
        if(resposta == 's'){
            String nome;
            do{
                System.out.print("\nNome novo:");
                nome=sc.nextLine();
            } while(!v.verificaString(nome,2));
            setNome(nome);
        }

        System.out.print("\nEditar numero de identificação fiscal? ");
        char resposta1 = v.verificaSimNao(sc);
        boolean disponivel = true;

        if(resposta1 == 's'){
            String nif;
            do{
                System.out.println("\nNumero de identificação fiscal novo:");
                nif = sc.nextLine();
                for (Cliente cliente : listaCliente) {
                    if (nif.equals(cliente.getNif())) {
                        System.out.println("Erro: Este NIF não está disponível.");
                        disponivel = false;
                    }
                }
            } while(!v.verificaNif(nif,listaCliente) || !disponivel);
            setNif(nif);
        }

        System.out.print("\nEditar localização? ");
        char resposta2 = v.verificaSimNao(sc);
        if(resposta2 == 's'){
            String localizacao;
            do{
                System.out.print("\nLocalização nova:");
                localizacao = sc.nextLine();
            } while(!v.verificaLocalizacao(localizacao));
            setLocalizacao(localizacao.toLowerCase());
        }
    }

    /**
     * Retorna uma representação textual do cliente.
     *
     * @return uma string contendo o nome, NIF e localização do cliente.
     */
    public String toString(){
        return "Nome: " + getNome() + "  NIF: " + getNif() + "  Localização: " + getLocalizacao();
    }

    /**
     * Retorna o nome do cliente.
     *
     * @return o nome do cliente.
     */
    public String getNome() {
        return nome;
    }

    /**
     * Define o nome do cliente.
     *
     * @param nome o novo nome do cliente.
     */
    public void setNome(String nome) {
        this.nome = nome;
    }

    /**
     * Retorna o número de identificação fiscal (NIF) do cliente.
     *
     * @return o NIF do cliente.
     */
    public String getNif() {
        return nif;
    }

    /**
     * Define o número de identificação fiscal (NIF) do cliente.
     *
     * @param nif o novo NIF do cliente.
     */
    public void setNif(String nif) {
        this.nif = nif;
    }

    /**
     * Retorna a localização do cliente.
     *
     * @return a localização do cliente.
     */
    public String getLocalizacao() {
        return localizacao;
    }

    /**
     * Define a localização do cliente.
     *
     * @param localizacao a nova localização do cliente.
     */
    public void setLocalizacao(String localizacao) {
        this.localizacao = localizacao;
    }

}