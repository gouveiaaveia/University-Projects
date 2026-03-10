/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.ArrayList;
import java.util.Scanner;
import java.io.Serializable;

/**
 * Representa uma fatura que contém informações do cliente, produtos, data, e valores relacionados a IVA.
 */
public class Fatura  implements Serializable{
    private String numeroFatura;
    private Cliente cliente;
    private String data;
    private ArrayList<Produtos> listaProdutos;


    private double valorComIVA;
    private double valorSemIVA;
    private double iva;

    /**
     * Construtor completo para inicializar uma fatura com número, cliente, data e produtos.
     *
     * @param numeroFatura o número da fatura.
     * @param cliente      o cliente associado à fatura.
     * @param data         a data da fatura no formato "dd-mm-aaaa".
     * @param produtos     a lista de produtos associados à fatura.
     */
    public Fatura(String numeroFatura, Cliente cliente, String data, ArrayList<Produtos> produtos){
        this.numeroFatura=numeroFatura;
        this.cliente=cliente;
        this.data=data;
        this.listaProdutos=produtos;
        this.valorComIVA=0.0;
        this.valorSemIVA=0.0;
    }

    /**
     * Construtor para criar uma fatura com apenas as informações do cliente.
     *
     * @param cliente o cliente associado à fatura.
     */
    public Fatura(Cliente cliente){
        this.numeroFatura= "";
        this.cliente = cliente;
        this.data= "";
        this.listaProdutos= new ArrayList<>();
        this.valorComIVA=0.0;
        this.valorSemIVA=0.0;
    }

    /**
     * Cria uma nova fatura com base nos dados fornecidos pelo usuário.
     *
     * @param dados         o objeto que contém informações de dados (produtos disponíveis).
     * @param sc            o objeto Scanner para entrada do usuário.
     * @param v             o objeto para validações.
     * @param numeroFatura  o número da fatura a ser criado.
     */
    public void criarFatura(Dados dados, Scanner sc, Verificacoes v, String numeroFatura){
        setNumeroFatura(numeroFatura);

        String data;
        do{
            System.out.print("Data da fatura (dd-mm-aaaa): ");
            data = sc.nextLine();
        }while(!v.verificaData(data));

        setData(data);

        System.out.print("Pretende adicionar algum produto? ");
        char opcao2;
        do{
            opcao2 = v.verificaSimNao(sc);

            if(opcao2=='s'){
                criarProduto(dados, sc, v, false, "");
            }else if(opcao2 == 'n'){
                calcularValoresIVA();
                break;
            }
            System.out.print("\nDeseja adicionar mais algum produto? ");
        }while(opcao2 == 's');
    }

    /**
     * Permite editar as informações da fatura, como número e lista de produtos.
     *
     * @param dados o objeto que contém informações de dados (produtos disponíveis).
     * @param sc    o objeto Scanner para entrada do usuário.
     * @param v     o objeto para validações.
     */
    public void editarFatura(Dados dados, Scanner sc, Verificacoes v){
        System.out.print("\nDeseja alterar o número da fatura? ");
        char opcao = v.verificaSimNao(sc);
        if(opcao== 's'){
            System.out.print("\nNúmero da fatura: ");
            setNumeroFatura(sc.nextLine());
        }
        System.out.print("\nPretende alterar os produtos da fatura? ");
        char opcao3 =  v.verificaSimNao(sc);

        if(opcao3== 's'){
            System.out.print("1 - Editar quantidade do produto\n2 - Remover produto\n3 - Adicionar produto\n");
            int opcao2;
            do{
                System.out.print("Opção: ");
                String valor = sc.nextLine();
                opcao2 = v.stringInteger(valor);
            }while(opcao2 != 1 && opcao2 != 2 && opcao2 !=3);

            if(opcao2 == 1){
                editarQuantidadeProduto(sc, v);
            }else if(opcao2==2){
                removerProduto(sc, v, dados);
            }else {
                adicionarProdutoFatura(dados, sc, v);
            }
            calcularValoresIVA();
        }
    }

    private void adicionarProdutoFatura(Dados dados, Scanner sc, Verificacoes v){
        boolean verificaCodigo = true;
        String opcao = v.verificaCodigo(sc);

        for(Produtos p: listaProdutos){
            if(p.getCodigo().equals(opcao)){
                System.out.println("\nO produto já existe na fatura, altere a quantidade.\n");
                editarQuantidadeProduto(sc, v);
            }else{
                verificaCodigo=false;
            }
        }

        if(!verificaCodigo) criarProduto(dados, sc, v, true, opcao);
    }

    private void editarQuantidadeProduto(Scanner sc, Verificacoes v){//só podemos editar a quantidade porque assim nao faria sentido ver se o codigo ja existe

        String codigo = v.verificaCodigo(sc);

        boolean encontrado = false;
        for(Produtos p: getListaProdutos()){
            if(p.getCodigo().equals(codigo)){
                int valor;
                String q = "\0";
                do{
                    System.out.print("\nQuantidade do produto: ");
                    q = sc.nextLine().trim();
                    valor = v.stringInteger(q);
                }while(valor == 0);
                p.setQuantidade(valor);
                encontrado = true;
            }
        }

        if(!encontrado){
            System.out.println("Produto não encontrado!");
        }
    }

    private void removerProduto(Scanner sc, Verificacoes v, Dados dados){
        String codigo = v.verificaCodigo(sc);
        boolean removido = false;
        for(Produtos p: getListaProdutos()){
            if(p.getCodigo().equals(codigo)){
                listaProdutos.remove(p);
                System.out.println("Produto removido com sucesso!");
                removido = true;
                break;
            }
        }
        if(!removido){
            System.out.println("Produto não encontrado!");
        }

        if(getListaProdutos().isEmpty()){
            dados.getFaturas().remove(this);
        }
    }

    private void criarProduto(Dados dados, Scanner sc, Verificacoes v, boolean codigoDado, String cod){
        String codigo = cod;

        if(!codigoDado){
            codigo = v.verificaCodigo(sc);
        }

        boolean verifica;
        Produtos produtoEncontrar = dados.encontrarProdutoDados(codigo);
        //verifica se o produto ja esta criado na lista dos dados

        if(produtoEncontrar != null){
            //se ja existir eu só vou pedir a quantidade do produto
            //produtoEncontrar vai estar à apontar para a mesma class do outro que ja existe
            verifica = true;
            boolean verificaListaProduto = false;
            int quantidade = produtoEncontrar.criarProdutosComum(verifica,codigo, sc, v);
            produtoEncontrar.setQuantidade(quantidade);
            getListaProdutos().add(produtoEncontrar);
        }
    }

    /**
     * Calcula os valores totais da fatura com e sem IVA, além do valor do IVA.
     */
    public void calcularValoresIVA(){
        setValorComIVA(0.0);
        setValorSemIVA(0.0);
        setIVA(0.0);
        for(Produtos p : getListaProdutos()){
            if(p==null)System.out.println("nuloo");
            setValorSemIVA(getValorSemIVA() + p.valorTotalSemIVA());
            setValorComIVA(getValorComIVA() + p.valorTotalComIVA(cliente.getLocalizacao()));
            setIVA(p.obterIVA(getCliente().getLocalizacao()));
        }
    }

    /**
     * Exibe as informações completas da fatura em um formato detalhado e legível.
     */
    public void faturaUnica() {
        double totalSemIVA = 0;
        double totalComIVA = 0;
        double valorTotalDoIVA = 0;

        System.out.println("\nInformações da fatura:\nNúmero da fatura: " + this.numeroFatura
                + "\nData da fatura (dd-mm-aaaa): " + this.data + " " +
                getCliente().toString()
                + "\n====================\nProdutos\n====================\n");

        String localizacao = getCliente().getLocalizacao();

        for (Produtos p : this.listaProdutos) {
            // Calcula os totais
            totalSemIVA += p.valorTotalSemIVA();
            double ivaProduto = p.obterIVA(localizacao);
            valorTotalDoIVA += ivaProduto;
            totalComIVA += p.valorTotalComIVA(localizacao);

            //imprime a informação do produto e os valores
            System.out.println(p  +
                    "\n Valor total sem IVA: " + p.valorTotalSemIVA() +
                    "\n Taxa de IVA: " + ivaProduto +
                    "\n Valor com IVA: " + p.valorComIVA(localizacao) +
                    "\n Valor total com IVA: " + p.valorTotalComIVA(localizacao));
        }

        // Exibe informações finais da fatura apenas uma vez
        System.out.println("\n====================\nInformação final da fatura\n====================\n" +
                "\n Valor total da fatura sem IVA: " + totalSemIVA +
                "\n Valor total do IVA: " + valorTotalDoIVA +
                "\n Valor total da fatura com IVA: " + totalComIVA);
    }


    /**
     * Retorna a representação textual da fatura, incluindo número e cliente.
     *
     * @return uma String representando a fatura.
     */
    @Override
    public String toString(){
        return "\nNúmero da fatura: " + this.numeroFatura + "\nInformação do cliente: " + getCliente().toString() + "\n";
    }

    /**
     * Retorna o número da fatura.
     *
     * @return o número da fatura.
     */
    public String getNumeroFatura() {
        return numeroFatura;
    }

    /**
     * Define o número da fatura.
     *
     * @param numeroFatura o número da fatura.
     */
    public void setNumeroFatura(String numeroFatura) {
        this.numeroFatura = numeroFatura;
    }

    /**
     * Retorna o cliente associado à fatura.
     *
     * @return o cliente associado à fatura.
     */
    public Cliente getCliente() {
        return cliente;
    }

    /**
     * Define o cliente associado à fatura.
     *
     * @param cliente o cliente associado à fatura.
     */
    public void setCliente(Cliente cliente) {
        this.cliente = cliente;
    }

    /**
     * Retorna a data da fatura.
     *
     * @return a data da fatura no formato "dd-mm-aaaa".
     */
    public String getData() {
        return data;
    }

    /**
     * Define a data da fatura.
     *
     * @param data a data da fatura no formato "dd-mm-aaaa".
     */
    public void setData(String data) {
        this.data = data;
    }

    /**
     * Retorna a lista de produtos associados à fatura.
     *
     * @return a lista de produtos.
     */
    public ArrayList<Produtos> getListaProdutos() {
        return listaProdutos;
    }

    /**
     * Define a lista de produtos associados à fatura.
     *
     * @param listaProdutos a nova lista de produtos.
     */
    public void setListaProdutos(ArrayList<Produtos> listaProdutos) {
        this.listaProdutos = listaProdutos;
    }

    /**
     * Retorna o valor total da fatura com IVA.
     *
     * @return o valor total com IVA.
     */
    public double getValorComIVA() {
        return valorComIVA;
    }

    /**
     * Define o valor total da fatura com IVA.
     *
     * @param valorComIVA o valor total com IVA.
     */
    public void setValorComIVA(double valorComIVA) {
        this.valorComIVA = valorComIVA;
    }

    /**
     * Retorna o valor total da fatura sem IVA.
     *
     * @return o valor total sem IVA.
     */
    public double getValorSemIVA() {
        return valorSemIVA;
    }

    /**
     * Define o valor total da fatura sem IVA.
     *
     * @param valorSemIVA o valor total sem IVA.
     */
    public void setValorSemIVA(double valorSemIVA) {
        this.valorSemIVA = valorSemIVA;
    }

    /**
     * Retorna o valor do IVA da fatura.
     *
     * @return o valor do IVA.
     */
    public double getIVA() {
        return iva;
    }

    /**
     * Define o valor do IVA da fatura.
     *
     * @param iva o valor do IVA.
     */
    public void setIVA(double iva) {
        this.iva = iva;
    }

}