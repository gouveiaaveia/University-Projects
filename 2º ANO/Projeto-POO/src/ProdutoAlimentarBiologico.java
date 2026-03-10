/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.util.ArrayList;
import java.io.Serializable;

public class ProdutoAlimentarBiologico extends ProdutoAlimentar implements Serializable{

    private final boolean biologico;

    /**
     * Construtor que inicializa o produto alimentar biológico com os detalhes fornecidos.
     *
     * @param nome           o nome do produto.
     * @param codigo         o código do produto.
     * @param descricao      a descrição do produto.
     * @param precoUnitario  o preço unitário do produto.
     * @param categoria      a categoria do produto.
     * @param certificacoes  a lista de certificações aplicáveis ao produto.
     */
    public ProdutoAlimentarBiologico(String nome, String codigo,String descricao, double precoUnitario, String categoria, ArrayList<String> certificacoes){
        super(nome,codigo,descricao,precoUnitario,categoria,certificacoes);
        this.biologico = true;
    }

    /**
     * Calcula o valor do produto com IVA incluído, aplicando um desconto especial
     * para produtos biológicos com base na localização fornecida.
     *
     * @param localizacao a localização para calcular o IVA (ex.: "portugal continental").
     * @return o valor do produto com IVA incluído.
     */
    @Override
    public double valorComIVA(String localizacao){
        return getPrecoUnitario() + (aplicarDescontoBiologico(localizacao) * getPrecoUnitario());
    }

    private double aplicarDescontoBiologico(String localizacao){
        return obterIVA(localizacao) - (double) (10 /100);
    }

    /**
     * Verifica se o produto é biológico.
     *
     * @return {@code true} se o produto é biológico; caso contrário, {@code false}.
     */
    public boolean isBiologico() {
        return biologico;
    }
}
