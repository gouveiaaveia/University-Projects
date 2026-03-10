/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */

/**
 * Representa uma tabela de taxas de IVA (Imposto sobre o Valor Acrescentado) aplicáveis
 * a diferentes tipos de produtos e localizações em Portugal.
 *
 * A classe permite definir e consultar taxas reduzidas, intermediárias, normais
 * e de prescrição para diferentes cenários. As taxas são armazenadas como inteiros
 * representando porcentagens (por exemplo, 23 para 23%).
 *
 * Principais funcionalidades:
 * - Criação de tabelas de IVA personalizadas com base em taxas específicas.
 * - Obtenção de tabelas de IVA predefinidas com base na localização e no tipo de produto.
 * - Conversão das taxas para valores decimais utilizáveis em cálculos.
 */

public class TabelaIVA {
    private int taxaReduzida;
    private int taxaIntermedia;
    private final int taxaNormal; //o valor não pode ser modificado depois desta class
    private int Taxaprescricao;

    /**
     * Construtor que inicializa uma tabela de IVA com taxas reduzida, intermediária e normal.
     *
     * @param taxaReduzida   a taxa reduzida de IVA (em porcentagem).
     * @param taxaIntermedia a taxa intermediária de IVA (em porcentagem).
     * @param taxaNormal     a taxa normal de IVA (em porcentagem).
     */
    public TabelaIVA(int taxaReduzida, int taxaIntermedia, int taxaNormal) {
        this.taxaReduzida = taxaReduzida;
        this.taxaIntermedia = taxaIntermedia;
        this.taxaNormal = taxaNormal;
    }

    /**
     * Construtor que inicializa uma tabela de IVA com taxa normal e taxa de prescrição.
     *
     * @param taxaNormal      a taxa normal de IVA (em porcentagem).
     * @param TaxaPrescricao  a taxa de prescrição de IVA (em porcentagem).
     */
    public TabelaIVA(int taxaNormal, int TaxaPrescricao) {
        this.taxaNormal = taxaNormal;
        this.Taxaprescricao = TaxaPrescricao;
    }


    /**
     * Obtém uma tabela de IVA predefinida com base na localização e no tipo de produto.
     *
     * @param localizacao a localização onde as taxas são aplicáveis
     *                    (ex.: "portugal continental", "madeira", "açores").
     * @param tipoProduto o tipo de produto (ex.: "alimentar" ou outro).
     * @return uma nova instância de {@code TabelaIVA} com taxas específicas.
     * @throws IllegalArgumentException se a localização for desconhecida.
     */
    public TabelaIVA getTabelaPorLocalizacao(String localizacao, String tipoProduto) {
        if(tipoProduto.equals("alimentar")){
            switch (localizacao) {
                case "portugal continental":
                    return new TabelaIVA(6, 13, 23);
                case "madeira":
                    return new TabelaIVA(5, 12, 22);
                case "açores":
                    return new TabelaIVA(4, 10, 18);
                default:
                    throw new IllegalArgumentException("Localização desconhecida");
            }
        }else{
            switch (localizacao){
                case "portugal continental":
                    return new TabelaIVA(6,23);
                case "madeira":
                    return new TabelaIVA(5, 23);
                case "açores":
                    return new TabelaIVA(4, 23);
                default:
                    throw new IllegalArgumentException("Localização desconhecida");
            }
        }
    }

    /**
     * Obtém a taxa reduzida de IVA como um valor decimal.
     *
     * @return a taxa reduzida de IVA (ex.: 0.06 para 6%).
     */
    public double getTaxaReduzida() { return (double) taxaReduzida / 100; }
    /**
     * Obtém a taxa intermediária de IVA como um valor decimal.
     *
     * @return a taxa intermediária de IVA (ex.: 0.13 para 13%).
     */
    public double getTaxaIntermedia() { return (double) taxaIntermedia / 100; }
    /**
     * Obtém a taxa normal de IVA como um valor decimal.
     *
     * @return a taxa normal de IVA (ex.: 0.23 para 23%).
     */
    public double getTaxaNormal() { return (double) taxaNormal / 100; }
    /**
     * Obtém a taxa de prescrição de IVA como um valor decimal.
     *
     * @return a taxa de prescrição de IVA (ex.: 0.23 para 23%).
     */
    public double getPrescricao() { return (double) Taxaprescricao / 100; }
}
