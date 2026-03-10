/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.Random;
import java.util.Scanner;
import java.io.Serializable;

/**
 * Classe abstrata que representa produtos com informações básicas como código, nome, descrição,
 * quantidade e preço unitário. Esta classe implementa Serializable.
 * Inclui métodos para manipular e acessar os atributos do produto.
 */
public abstract class Produtos implements Serializable{
    protected String codigo;
    protected String nome;
    protected String descricao;
    protected int quantidade;
    protected double precoUnitario;

    /**
     * Construtor que inicializa todos os atributos do produto com os valores fornecidos.
     *
     * @param codigo        o código do produto.
     * @param nome          o nome do produto.
     * @param descricao     a descrição do produto.
     * @param precoUnitario o preço unitário do produto.
     */
    public Produtos(String codigo, String nome, String descricao,double precoUnitario){
        this.codigo = codigo;
        this.nome = nome;
        this.descricao = descricao;
        this.quantidade = 0;
        this.precoUnitario = precoUnitario;
    }

    /**
     * Construtor padrão que inicializa os atributos do produto com valores padrão.
     * Código, nome e descrição são inicializados como strings vazias,
     * quantidade como 0 e preço unitário como 0.0.
     */
    public Produtos(){
        this.codigo = "";
        this.nome = "";
        this.descricao = "";
        this.quantidade = 0;
        this.precoUnitario = 0;
    }

    protected int criarProdutosComum(boolean verifica, String codigo, Scanner sc, Verificacoes v){
        int valor;
        do{
            System.out.print("Quantidade do produto: ");
            String q = sc.nextLine();
            valor = v.stringInteger(q);
        }while(valor == 0);
        setQuantidade(valor);
        return (valor);
    }

    protected abstract double valorTotalComIVA(String localizacao);
    protected abstract double valorTotalSemIVA();
    protected abstract double obterIVA(String localizacao);
    protected abstract double valorComIVA(String localizacao);

    /**
     * Retorna uma representação em forma de string do produto, contendo
     * informações sobre o código, nome, preço unitário e quantidade.
     *
     * @return uma string com as informações básicas do produto.
     */
    public String toString(){
        return "Código: " + getCodigo() + "  Nome: " + getNome() + "  Preço Unitário: " + getPrecoUnitario() + "  Quantidade: " + getQuantidade();
    };

    /**
     * Obtém o código do produto.
     *
     * @return o código do produto.
     */
    public String getCodigo() {
        return codigo;
    }
    /**
     * Define o código do produto.
     *
     * @param codigo o novo código do produto.
     */
    public void setCodigo(String codigo) {
        this.codigo = codigo;
    }
    /**
     * Obtém o nome do produto.
     *
     * @return o nome do produto.
     */
    public String getNome() {
        return nome;
    }
    /**
     * Define o nome do produto.
     *
     * @param nome o novo nome do produto.
     */
    public void setNome(String nome) {
        this.nome = nome;
    }
    /**
     * Obtém a descrição do produto.
     *
     * @return a descrição do produto.
     */
    public String getDescricao() {
        return descricao;
    }
    /**
     * Define a descrição do produto.
     *
     * @param descricao a nova descrição do produto.
     */
    public void setDescricao(String descricao) {
        this.descricao = descricao;
    }
    /**
     * Obtém a quantidade disponível do produto.
     *
     * @return a quantidade do produto.
     */
    public int getQuantidade() {
        return quantidade;
    }
    /**
     * Define a quantidade disponível do produto.
     *
     * @param quantidade a nova quantidade do produto.
     */
    public void setQuantidade(int quantidade) {
        this.quantidade = quantidade;
    }
    /**
     * Obtém o preço unitário do produto.
     *
     * @return o preço unitário do produto.
     */
    public double getPrecoUnitario() {
        return precoUnitario;
    }
    /**
     * Define o preço unitário do produto.
     *
     * @param precoUnitario o novo preço unitário do produto.
     */
    public void setPrecoUnitario(double precoUnitario) {
        this.precoUnitario = precoUnitario;
    }
}