/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.ArrayList;
import java.util.Scanner;
import java.io.Serializable;

/**
 * Classe que gerencia os dados de clientes, faturas e produtos.
 */
public class Dados implements Serializable{
    private ArrayList<Cliente> clientes;
    private ArrayList<Fatura> faturas;
    private ArrayList<Produtos> produtos;

    /**
     * Construtor padrão que inicializa as listas de clientes, faturas e produtos.
     */
    public Dados(){
        this.clientes = new ArrayList<>();
        this.faturas = new ArrayList<>();
        this.produtos= new ArrayList<>();
    }

    /**
     * Adiciona um cliente à lista de clientes.
     *
     * @param cliente o cliente a ser adicionado.
     */
    public void adicionarCliente(Cliente cliente){
        this.clientes.add(cliente);
    }


    /**
     * Encontra e retorna um cliente com base no NIF fornecido.
     *
     * @param nif o NIF do cliente.
     * @return o cliente correspondente ou null se não encontrado.
     */
    public Cliente encontrarCliente(String nif){
        for(Cliente cliente: clientes){
            if(nif.equals(cliente.getNif())) return cliente;
        }
        return null;
    }

    /**
     * Exibe a lista de todos os clientes cadastrados.
     */
    public void mostrarListaClientes(){
        for(Cliente c : clientes){
            System.out.println(c.toString());
        }
    }

    /**
     * Adiciona uma fatura à lista de faturas.
     *
     * @param fatura a fatura a ser adicionada.
     */
    public void adicionarFatura(Fatura fatura){
        this.faturas.add(fatura);
    }

    /**
     * Encontra e retorna uma fatura com base no número da fatura fornecido.
     *
     * @param sc Scanner para leitura da entrada do usuário.
     * @return a fatura correspondente ou null se não encontrada.
     */
    public Fatura encontrarFatura(Scanner sc){
        System.out.print("Número da fatura: ");
        String numeroFatura = sc.nextLine();
        boolean encontrada = false;
        for(Fatura f: faturas){
            if(f.getNumeroFatura().equals(numeroFatura)){
                encontrada = true;
                return f;
            }
        }
        if(!encontrada){
            System.out.println("Fatura não encontrada");
        }
        return null;
    }

    /**
     * Exibe os detalhes de uma fatura com base no número fornecido.
     *
     * @param sc Scanner para leitura da entrada do usuário.
     */
    public void mostrarFatura(Scanner sc){
        System.out.print("Número da fatura: ");
        String numeroFatura = sc.nextLine();
        boolean encontrada = false;
        for(Fatura f: faturas){
            if(f.getNumeroFatura().equals(numeroFatura)){
                f.faturaUnica();
                encontrada = true;
                break;
            }
        }
        if(!encontrada){
            System.out.println("Fatura não encontrada!");
        }
    }

    /**
     * Exibe a lista de todos os produtos cadastrados.
     */
    public void mostrarProdutos(){
        if(produtos.isEmpty())System.out.println("vazio");
        for(Produtos p:produtos){
            System.out.println(p.getNome());
        }
    }

    /**
     * Exibe a lista de todas as faturas cadastradas com detalhes.
     */
    public void mostrarListaFaturas(){
        if(getFaturas().isEmpty()){
            System.out.println("Sem nenhuma fatura registada no sistema!");
            return;
        }
        for(Fatura f : faturas){
            f.calcularValoresIVA();
            System.out.println(f + "Número de produtos: " + f.getListaProdutos().size() + "\nValor total sem IVA: " +
                    f.getValorSemIVA() + "\nValor total com IVA: " + f.getValorComIVA());
        }
    }

    /**
     * Exibe estatísticas relacionadas às faturas e produtos cadastrados.
     */
    public void estatisticas(){
        int numeroFaturas= getFaturas().size();
        int numeroProdutos= getProdutos().size();
        double totalSemIVA=calculaTotalSemIVA();
        double totalComIVA=calculaTotalComIVA();
        double totalIVA=calculaIVA();
        System.out.printf("Faturas: %d\nProdutos: %d\nValor total sem IVA: %f\nValor total com IVA: %f\nValor total do IVA: %f", numeroFaturas,numeroProdutos,totalSemIVA,totalComIVA,totalIVA);

    }

    private double calculaTotalSemIVA(){
        double total=0.0;
        for(Fatura f: getFaturas()){
            total+=f.getValorSemIVA();
        }
        return total;
    }
    private double calculaTotalComIVA(){
        double total=0.0;
        for(Fatura f: getFaturas()){
            total+=f.getValorComIVA();
        }
        return total;
    }
    private double calculaIVA(){
        double total=0.0;
        for(Fatura f: getFaturas()){
            total+=f.getIVA();
        }
        return total;
    }

    /**
     * Adiciona um produto à lista de produtos.
     *
     * @param produto o produto a ser adicionado.
     */
    public void adicionarPordutosDados(Produtos produto){
        System.out.println("Produto adicionado");
        this.produtos.add(produto);
    }

    /**
     * Encontra e retorna um produto com base no código fornecido.
     *
     * @param codigo o código do produto.
     * @return o produto correspondente ou null se não encontrado.
     */
    public Produtos encontrarProdutoDados(String codigo){
        for(Produtos p: this.produtos){
            if(codigo.equalsIgnoreCase(p.getCodigo())){
                System.out.println("\nProduto já existe");
                return p;
            }
        }
        System.out.println("\nProduto não existe");
        return null;
    }

    /**
     * Retorna a lista de clientes cadastrados.
     *
     * @return a lista de clientes.
     */
    public ArrayList<Cliente> getClientes() {
        return clientes;
    }

    /**
     * Define a lista de clientes cadastrados.
     *
     * @param clientes a nova lista de clientes.
     */
    public void setClientes(ArrayList<Cliente> clientes) {
        this.clientes = clientes;
    }

    /**
     * Retorna a lista de faturas cadastradas.
     *
     * @return a lista de faturas.
     */
    public ArrayList<Fatura> getFaturas() {
        return faturas;
    }

    /**
     * Define a lista de faturas cadastradas.
     *
     * @param faturas a nova lista de faturas.
     */
    public void setFaturas(ArrayList<Fatura> faturas) {
        this.faturas = faturas;
    }

    /**
     * Retorna a lista de produtos cadastrados.
     *
     * @return a lista de produtos.
     */
    public ArrayList<Produtos> getProdutos() {
        return produtos;
    }

    /**
     * Define a lista de produtos cadastrados.
     *
     * @param produtos a nova lista de produtos.
     */
    public void setProdutos(ArrayList<Produtos> produtos) {
        this.produtos = produtos;
    }
}