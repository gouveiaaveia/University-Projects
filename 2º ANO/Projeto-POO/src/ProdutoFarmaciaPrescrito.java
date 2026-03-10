/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.Scanner;
import java.io.Serializable;

/**
 * Representa um produto de farmácia prescrito, contendo informações específicas como o nome do médico que prescreveu.
 */
public class ProdutoFarmaciaPrescrito extends Produtos implements Serializable{

    private String nomeMedico;

    /**
     * Construtor que inicializa um produto de farmácia prescrito com os dados fornecidos.
     *
     * @param codigo o código do produto.
     * @param nome o nome do produto.
     * @param descricao a descrição do produto.
     * @param precoUnitario o preço unitário do produto.
     * @param medico o nome do médico que prescreveu o produto.
     */
    public ProdutoFarmaciaPrescrito(String codigo, String nome, String descricao,double precoUnitario,String medico) {
        super(codigo,nome,descricao,precoUnitario);
        this.nomeMedico =medico;
    }

    /**
     * Retorna uma representação textual do produto prescrito.
     *
     * @return uma string contendo as informações do produto prescrito.
     */
    public String toString(){
        String str="";
        str+=super.toString();
        str+=" Produto Farmacia Prescrito\n";
        str+="Médico: "+ getNomeMedico() +"\n";
        return str;
    }

    /**
     * Calcula a taxa de IVA aplicável ao produto com base na localização.
     *
     * @param localizacao a localização onde o produto será vendido.
     * @return a taxa de IVA para o produto.
     */
    public double obterIVA(String localizacao){
        TabelaIVA tabela= new TabelaIVA(0,0);
        TabelaIVA tabelaValores= tabela.getTabelaPorLocalizacao(localizacao, "farmacia");
        return tabelaValores.getPrescricao();
    }

    /**
     * Calcula o valor do produto com IVA por unidade.
     *
     * @param localizacao a localização onde o produto será vendido.
     * @return o valor unitário do produto com IVA.
     */
    @Override
    public double valorComIVA(String localizacao){ //iva por cada um produtor
        return getPrecoUnitario() + (getPrecoUnitario() * obterIVA(localizacao));

    }

    /**
     * Calcula o valor total do produto sem IVA.
     *
     * @return o valor total do produto sem IVA.
     */
    @Override
    public double valorTotalSemIVA(){
        return (double) getQuantidade() * getPrecoUnitario();
    }

    /**
     * Calcula o valor total do produto com IVA.
     *
     * @param localizacao a localização onde o produto será vendido.
     * @return o valor total do produto com IVA.
     */
    @Override
    public double valorTotalComIVA(String localizacao){
        return getQuantidade() * valorComIVA(localizacao);
    }

    /**
     * Retorna o nome do médico que prescreveu o produto.
     *
     * @return o nome do médico.
     */
    public String getNomeMedico() {
        return nomeMedico;
    }

    /**
     * Define o nome do médico que prescreveu o produto.
     *
     * @param nomeMedico o nome do médico.
     */
    public void setNomeMedico(String nomeMedico) {
        this.nomeMedico = nomeMedico;
    }
}