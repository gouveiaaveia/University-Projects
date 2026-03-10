/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */

import java.util.Scanner;

/**
 * Classe principal do programa POO Financial Services.
 * Responsável por executar o menu principal e as funcionalidades associadas.
 */
public class POOFS {
    /**
     * Método principal do programa.
     * Inicializa os componentes necessários, verifica os ficheiros de dados e executa o menu principal.
     *
     * @param args Argumentos da linha de comando (não utilizados).
     */
    public static void main(String[] args) {
        //Gui gui = new Gui();
        //gui.criarMenu();

        Scanner sc = new Scanner(System.in);
        Verificacoes v = new Verificacoes();
        Dados dados = new Dados();

        boolean continuar = true;

        //nome dos ficheiros
        String ficheiroTexto = "ficheiro.text";
        String ficheiroObj = "ficheiroObj.obj";

        Ficheiros f = new Ficheiros(ficheiroTexto, ficheiroObj);

        if(!f.verificaFicheiro()){ //caso do ficheiro de objetos não existir
            f.lerFicheiroTexto(dados);
        }else{
            f.lerFicheiroObjetos(dados);
        }

        do {
            System.out.println("\n\n=======================");
            System.out.println("POO Financial Services");
            System.out.println("=======================\n");
            System.out.println("""
                    MENU:
                    1 - Criar cliente
                    2 - Editar cliente
                    3 - Lista de clientes
                    4 - Criar fatura
                    5 - Editar fatura
                    6 - Lista de faturas
                    7 - Visualizar fatura
                    8 - Importar faturas
                    9 - Exportar faturas
                    10 - Estatísticas
                    11 - Sair""");
            System.out.print("=======================\nOpção: ");

            String op = sc.nextLine();
            int opcao = v.opcaoMenu(op);

            switch(opcao) {
                case 1:
                    System.out.println("\nCriar cliente: ");
                    Cliente cliente = new Cliente();
                    cliente.criarCliente(dados.getClientes(), sc, v);
                    dados.adicionarCliente(cliente);
                    System.out.println("Cliente adicionado com sucesso!");
                    break;

                case 2:
                    if(dados.getClientes().isEmpty())System.out.print("\nErro: Lista vazia");
                    else{
                        String nif;
                        do {
                            System.out.print("\nNIF do Cliente que deseja editar: ");
                            nif = sc.nextLine();
                        } while (!v.verificaNif(nif, dados.getClientes()));

                        Cliente clienteEditar = dados.encontrarCliente(nif);

                        if(clienteEditar==null)System.out.print("Erro: Cliente não encontrado, tente de novo\n");
                        else clienteEditar.EditaCliente(dados.getClientes(), sc, v);
                    }
                    break;

                case 3:
                    System.out.println("Lista de clientes:\n");
                    dados.mostrarListaClientes();
                    break;

                case 4:
                    System.out.println("\nCriar fatura:");
                    System.out.print("NIF do cliente: ");
                    String nif = sc.nextLine();

                    if(dados.getClientes().isEmpty()){
                        System.out.println("Sem nenhum cliente registado!");
                        break;
                    }

                    boolean clienteEncontrado = false;// Variável de controle
                    boolean existe;
                    String n;

                    for(Cliente c : dados.getClientes()){
                        if(c.getNif().equals(nif)){
                            Fatura fatura = new Fatura(c);
                            do{
                                existe = false;
                                System.out.print("Número da fatura: ");
                                n = sc.nextLine();
                                for(Fatura f1: dados.getFaturas()){
                                    if (n.equals(f1.getNumeroFatura())){
                                        System.out.println("\nFatura já existe!!");
                                        existe = true;
                                        break;
                                    }
                                }
                            }while(existe);
                            fatura.criarFatura(dados,sc, v, n);
                            dados.adicionarFatura(fatura);
                            clienteEncontrado = true;  // Cliente foi encontrado
                            break;
                        }
                    }

                    if (!clienteEncontrado) {  // Só exibe a mensagem se o cliente não foi encontrado
                        System.out.println("Cliente não encontrado!");
                    }
                    break;

                case 5:
                    System.out.println("Editar fatura");
                    Fatura f1 = dados.encontrarFatura(sc);
                    if(f1 != null) {
                        f1.editarFatura(dados, sc, v);
                    }
                    break;
                case 6:
                    System.out.println("Lista de faturas:");
                    dados.mostrarListaFaturas();
                    break;

                case 7:
                    dados.mostrarFatura(sc);
                    break;

                case 8:
                    System.out.print("Nome do ficheiro que deseja importar: ");
                    String nomeFicheiroImportacao = sc.nextLine();
                    nomeFicheiroImportacao += ".text";
                    Ficheiros fFaturasImportacao = new Ficheiros(nomeFicheiroImportacao);
                    fFaturasImportacao.lerFicheiroFaturas(dados);
                    System.out.print("Ficheiro importado com sucesso!!");
                    break;

                case 9:
                    System.out.print("Nome do ficheiro para exportação: ");
                    String nomeFicheiroExportacao = sc.nextLine();
                    nomeFicheiroExportacao += ".text";
                    Ficheiros fFaturasExportacao = new Ficheiros(nomeFicheiroExportacao);
                    fFaturasExportacao.escreverFicheiroFaturas(dados);
                    System.out.print("Ficheiro exportado com sucesso!!");
                    break;

                case 10:
                    System.out.print("Estatisticas:\n");
                    dados.estatisticas();
                    break;
                case 11:
                    System.out.println("Saindo...");
                    continuar = false; // Encerra o loop
                    f.escreverFicheiroObjetos(dados);
                    break;

                default:
                    System.out.println("Opção inválida! Tente novamente.\n");
                    break;
            }
        } while (continuar); // Repete enquanto `continuar` for verdadeiro

        sc.close();
    }
}