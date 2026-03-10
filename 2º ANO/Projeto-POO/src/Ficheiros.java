/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;


/**
 * Classe responsável pela manipulação de ficheiros de texto e objetos.
 */
public class Ficheiros {
    private final String caminhoRelativoFicheiro;
    private final String caminhoFicheiroObjetos;
    private final String caminhoFicheiroFaturas;

    /**
     * Construtor para inicializar caminhos de ficheiros de texto e objetos.
     *
     * @param caminhoRelativoFicheiro Caminho relativo do ficheiro de texto.
     * @param caminhoFicheiroObjetos Caminho do ficheiro de objetos.
     */
    public Ficheiros(String caminhoRelativoFicheiro, String caminhoFicheiroObjetos) {
        this.caminhoRelativoFicheiro = caminhoRelativoFicheiro;
        this.caminhoFicheiroObjetos = caminhoFicheiroObjetos;
        this.caminhoFicheiroFaturas = "";
    }

    /**
     * Construtor para inicializar o caminho de ficheiros de faturas.
     *
     * @param caminhoFicheiroFaturas Caminho do ficheiro de faturas.
     */
    public Ficheiros(String caminhoFicheiroFaturas) {
        this.caminhoRelativoFicheiro = "";
        this.caminhoFicheiroObjetos = "";
        this.caminhoFicheiroFaturas = caminhoFicheiroFaturas;
    }

    /**
     * Verifica a existência do ficheiro de objetos.
     *
     * @return {@code true} se o ficheiro existe, caso contrário {@code false}.
     */
    public boolean verificaFicheiro() {
        return new File(this.caminhoFicheiroObjetos).exists();
    }

    /**
     * Lê dados de um ficheiro de texto e adiciona ao objeto {@link Dados}.
     *
     * @param dados Objeto {@link Dados} onde os dados serão armazenados.
     */
    public void lerFicheiroTexto(Dados dados) {
        File f = new File(this.caminhoRelativoFicheiro);

        if (!f.exists() || !f.isFile()) {
           System.out.print("\nFicheiro não existe.");
           return;
        }

        try (BufferedReader br = new BufferedReader(new FileReader(f))) {
            String line;
            while ((line = br.readLine()) != null) {
                switch (line) {
                    case "Clientes":
                        lerClientes(dados, br);
                        break;
                    case "Produtos":
                        lerProdutos(dados, br);
                        break;
                    case "Fatura":
                        lerFaturas(dados, br);
                        break;
                    default:
                        System.out.println("Seção desconhecida: " + line);
                        break;
                }
            }
        } catch (IOException ex) {
            System.out.print("\nErro ao ler o ficheiro de texto: " + ex.getMessage());
        }
    }

    /**
     * Lê faturas de um ficheiro de texto e adiciona ao objeto {@link Dados}.
     *
     * @param dados Objeto {@link Dados} onde os dados serão armazenados.
     */
    public void lerFicheiroFaturas(Dados dados){
        File f = new File(this.caminhoFicheiroFaturas);

        if (!f.exists() || !f.isFile()) {
            System.out.println("Ficheiro não existe!!");
            return;
        }

        try (BufferedReader br = new BufferedReader(new FileReader(f))) {

            lerFaturas(dados, br);

        } catch (IOException ex) {
            System.out.print("\nErro ao ler o ficheiro de texto: " + ex.getMessage());
        }
    }

    /**
     * Escreve as faturas no ficheiro de texto.
     *
     * @param dados Objeto {@link Dados} contendo as faturas a serem escritas.
     */
    public void escreverFicheiroFaturas(Dados dados){
        File f = new File(this.caminhoFicheiroFaturas);
        lerFicheiroFaturas(dados); //primeiro lê o ficheiro, guarda os dados e só depois o guarda para não perder informação

        try{
            FileWriter fw = new FileWriter(f, false);
            BufferedWriter bw = new BufferedWriter(fw);
            escreverFaturas(dados, bw);
            bw.close();
        }catch (IOException ex){
            System.out.println("Erro a escrever no ficheiro!");
        }
    }


    private void lerClientes(Dados dados, BufferedReader br) throws IOException {
        String line;
        while ((line = br.readLine()) != null) {
            if (line.equals("-")) break;
            String[] listaDadosClientes = line.split("/");
            Cliente clienteNovo = new Cliente(listaDadosClientes[0], listaDadosClientes[1], listaDadosClientes[2]);
            dados.adicionarCliente(clienteNovo);
        }
    }

    private void lerProdutos(Dados dados, BufferedReader br) throws IOException {
        String line;
        while ((line = br.readLine()) != null) {
            if (line.equals("-")) break;
            String[] listaDadosProdutos = line.split("/", -1); // Preserva espaços vazios
            switch (listaDadosProdutos[0]) {
                case "alimentar":
                    ArrayList<String> certificacoes = new ArrayList<>(Arrays.asList(listaDadosProdutos[6].split(",")));
                    ProdutoAlimentar p1 = new ProdutoAlimentar(
                            listaDadosProdutos[1], listaDadosProdutos[2], listaDadosProdutos[3],
                            Double.parseDouble(listaDadosProdutos[4]),
                            listaDadosProdutos[5],certificacoes
                    );
                    dados.adicionarPordutosDados(p1);
                    break;
                case "biologico":
                    certificacoes = new ArrayList<>(Arrays.asList(listaDadosProdutos[6].split(",")));
                    ProdutoAlimentarBiologico p2 = new ProdutoAlimentarBiologico(
                            listaDadosProdutos[1], listaDadosProdutos[2], listaDadosProdutos[3],
                            Double.parseDouble(listaDadosProdutos[4]),
                            listaDadosProdutos[5],certificacoes);

                    dados.adicionarPordutosDados(p2);
                    break;
                case "farmacia":
                    ProdutoFarmacia p3 = new ProdutoFarmacia(
                            listaDadosProdutos[1], listaDadosProdutos[2], listaDadosProdutos[3],
                            Double.parseDouble(listaDadosProdutos[4]),
                            listaDadosProdutos[5]
                    );
                    dados.adicionarPordutosDados(p3);
                    break;
                default:
                    ProdutoFarmaciaPrescrito p4 = new ProdutoFarmaciaPrescrito(
                            listaDadosProdutos[1], listaDadosProdutos[2], listaDadosProdutos[3],
                            Double.parseDouble(listaDadosProdutos[4]),
                            listaDadosProdutos[5]
                    );
                    dados.adicionarPordutosDados(p4);
                    break;
            }
        }
    }

    private void lerFaturas(Dados dados, BufferedReader br) throws IOException {
        String line;
        boolean existe;
        while ((line = br.readLine()) != null) {
            existe = false;
            String[] listaDadosFatura = line.split(";");
            String[] fatura = listaDadosFatura[0].split("/");
            String[] produtos = listaDadosFatura[1].split("/");

            for(Fatura f: dados.getFaturas()){
                if (fatura[0].equals(f.getNumeroFatura())){
                    existe = true;
                    break;
                }
            }

            if(existe){
                continue; //caso já exista a fatura não adiciona aos dados
            }

            Cliente cliente = dados.encontrarCliente(fatura[1]);
            ArrayList<Produtos> listaProdutos = new ArrayList<>();

            for (String i : produtos) {
                String[] valores = i.split(",");
                Produtos produto = dados.encontrarProdutoDados(valores[0]);

                produto.setQuantidade(Integer.parseInt(valores[1]));

                listaProdutos.add(produto);
            }

            Fatura f = new Fatura(fatura[0], cliente, fatura[2], listaProdutos);
            f.calcularValoresIVA();
            dados.getFaturas().add(f);
        }
    }

    private void escreverFaturas(Dados dados, BufferedWriter bw) throws IOException {
        for(Fatura f : dados.getFaturas()){
            bw.write(f.getNumeroFatura() + "/" + f.getCliente().getNif() + "/" +
                    f.getData() + ";");
            int count = 0;
            for(Produtos p : f.getListaProdutos()){
                if(count > 0){
                    bw.write("/" + p.getCodigo() + "," + p.getQuantidade());
                }else{
                    count += 1;
                    bw.write(p.getCodigo() + "," + p.getQuantidade());
                }
            }
            bw.newLine();
        }
    }

    /**
     * Lê os objetos serializados de um ficheiro e adiciona ao objeto {@link Dados}.
     *
     * @param dados Objeto {@link Dados} onde os dados serão armazenados.
     */
    public void lerFicheiroObjetos(Dados dados){
        try{
            FileInputStream fis = new FileInputStream(this.caminhoFicheiroObjetos);
            ObjectInputStream ois = new ObjectInputStream(fis);
            ArrayList<Cliente> clientes = (ArrayList<Cliente>) ois.readObject();
            ArrayList<Produtos> produtos = (ArrayList<Produtos>) ois.readObject();
            ArrayList<Fatura> faturas = (ArrayList<Fatura>) ois.readObject();
            dados.setClientes(clientes);
            dados.setProdutos(produtos);
            dados.setFaturas(faturas);
            ois.close();
        }catch (FileNotFoundException ex){
            System.out.print("\nFicheiro não encontrado: " + ex.getMessage());
        }catch (IOException ex){
            System.out.print("\nErro ao ler o ficheiro: " + ex.getMessage());
        }catch (ClassNotFoundException ex){
            System.out.print("\nClasse não encontrada: ");
        }
    }

    /**
     * Escreve os objetos serializados de {@link Dados} no ficheiro.
     *
     * @param dados Objeto {@link Dados} contendo os dados a serem serializados.
     */
    public void escreverFicheiroObjetos(Dados dados) {
        try (FileOutputStream fos = new FileOutputStream(this.caminhoFicheiroObjetos);
             ObjectOutputStream oos = new ObjectOutputStream(fos)) {
            oos.writeObject(dados.getClientes());
            oos.writeObject(dados.getProdutos());
            oos.writeObject(dados.getFaturas());
            oos.close();
        } catch (FileNotFoundException ex) {
            System.out.print("\nFicheiro não encontrado: " + ex.getMessage());
        } catch (IOException ex) {
            System.out.print("\nErro ao escrever no ficheiro");
        }
    }
}