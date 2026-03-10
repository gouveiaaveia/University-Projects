/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.ArrayList;
import java.util.Scanner;
import java.io.Serializable;

/**
 * Classe que representa produtos alimentares, estendendo a classe Produtos.
 * Inclui características específicas como categoria, certificações e tipo de taxa IVA.
 */
public class ProdutoAlimentar extends Produtos implements Serializable{

    private enum TipoTaxa {
        Reduzida,
        Intermedia,
        Normal
    }

    protected TipoTaxa tipoTaxa;
    protected String categotia;
    protected ArrayList<String> certificacoes;


    /**
     * Construtor que inicializa todos os atributos do produto alimentar com os valores fornecidos.
     *
     * @param nome           o nome do produto.
     * @param codigo         o código do produto.
     * @param descricao      a descrição do produto.
     * @param precoUnitario  o preço unitário do produto.
     * @param categoria      a categoria do produto alimentar.
     * @param certificacoes  as certificações do produto alimentar.
     */
    public ProdutoAlimentar(String nome, String codigo,String descricao, double precoUnitario, String categoria,ArrayList<String> certificacoes){
        super(nome,codigo,descricao,precoUnitario);
        this.categotia=categoria;
        this.certificacoes=certificacoes;
        determinarTipoTaxaIVA();
    }

    /**
     * Calcula o preço unitário do produto com IVA com base na localização.
     * Aplica regras específicas para certificações ou categoria "vinho".
     *
     * @param localizacao a localização usada para determinar a taxa de IVA.
     * @return o preço unitário com IVA.
     */
    @Override
    public double valorComIVA(String localizacao){
        if(getCertificacoes().size() == 4){
            return getPrecoUnitario() + (extraCertificacoes(localizacao) * getPrecoUnitario());
        }else if(getCategotia().equalsIgnoreCase("vinho")){
            return getPrecoUnitario() + (extraCategoriaVinho(localizacao) * getPrecoUnitario());
        }

        return getPrecoUnitario() + (obterIVA(localizacao) * getPrecoUnitario());
    }

    /**
     * Calcula o valor total do produto sem IVA.
     *
     * @return o valor total sem IVA.
     */
    @Override
    public double valorTotalSemIVA(){
        return getQuantidade() * getPrecoUnitario();
    }

    /**
     * Calcula o valor total do produto com IVA com base na localização.
     *
     * @param localizacao a localização usada para determinar a taxa de IVA.
     * @return o valor total com IVA.
     */
    @Override
    public double valorTotalComIVA(String localizacao){
        return getQuantidade() * valorComIVA(localizacao);
    }

    /**
     * Obtém a taxa de IVA aplicável com base na localização e tipo de taxa.
     *
     * @param localizacao a localização usada para determinar a taxa de IVA.
     * @return a taxa de IVA aplicável.
     */
    @Override
    public double obterIVA(String localizacao) {

        TabelaIVA tabelaBase = new TabelaIVA(0,0,0);
        TabelaIVA tabela = tabelaBase.getTabelaPorLocalizacao(localizacao.toLowerCase(), "alimentar");

        switch (tipoTaxa) {
            case Reduzida:
                return tabela.getTaxaReduzida();
            case Intermedia:
                return tabela.getTaxaIntermedia();
            default:
                return tabela.getTaxaNormal();
        }
    }

    /**
     * Determina o tipo de taxa de um produto, baseado nas certificações e categoria
     */
    public void determinarTipoTaxaIVA(){
        if(!certificacoes.isEmpty()){
            tipoTaxa = TipoTaxa.Reduzida;
        }else if(getCategotia().equals("congelados") || getCategotia().equals("enlatados") || getCategotia().equals("vinho")){
            tipoTaxa = TipoTaxa.Intermedia;
        }else{
            tipoTaxa = TipoTaxa.Normal;
        }
    }

    protected double extraCategoriaVinho(String localizacao){
        return obterIVA(localizacao) + (double) (1 /100);
    }

    protected double extraCertificacoes(String localizacao){
        return obterIVA(localizacao) - (double) (1/100);
    }

    /**
     * Retorna uma representação em forma de string do produto alimentar.
     * Inclui as informações básicas herdadas da classe Produtos.
     *
     * @return uma string representando o produto alimentar.
     */
    public String toString(){
        return super.toString();
    }

    /**
     * Obtém o tipo de taxa IVA aplicado ao produto alimentar.
     *
     * @return o tipo de taxa IVA.
     */
    public TipoTaxa getTipoTaxa() {
        return tipoTaxa;
    }

    /**
     * Define o tipo de taxa IVA aplicado ao produto alimentar.
     *
     * @param tipoTaxa o novo tipo de taxa IVA.
     */
    public void setTipoTaxa(TipoTaxa tipoTaxa) {
        this.tipoTaxa = tipoTaxa;
    }

    /**
     * Obtém a categoria do produto alimentar.
     *
     * @return a categoria do produto.
     */
    public String getCategotia() {
        return categotia;
    }

    /**
     * Define a categoria do produto alimentar.
     *
     * @param categotia a nova categoria do produto.
     */
    public void setCategotia(String categotia) {
        this.categotia = categotia;
    }

    /**
     * Obtém a lista de certificações do produto alimentar.
     *
     * @return uma lista de certificações.
     */
    public ArrayList<String> getCertificacoes() {
        return certificacoes;
    }

    /**
     * Define a lista de certificações do produto alimentar.
     *
     * @param certificacoes a nova lista de certificações.
     */
    public void setCertificacoes(ArrayList<String> certificacoes) {
        this.certificacoes = certificacoes;
    }
}