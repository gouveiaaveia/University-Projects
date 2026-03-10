/**
 * @autor Francisco Gouveia e Ricardo Domingues
 * @version 1.0
 */
import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import javax.swing.JOptionPane;

public class Gui {

    private Dados dados;  // Declarar dados no nível da classe
    private JTextField textFieldNome, textFieldNif;
    private JComboBox<String> textFieldLoc;

    public void criarMenu() {
        dados = new Dados();  // Inicializar dados
        String ficheiroTexto = "ficheiro.text";
        String ficheiroObj = "ficheiroObj.obj";

        Ficheiros f = new Ficheiros(ficheiroTexto, ficheiroObj);

        if (!f.verificaFicheiro()) {  // Caso o ficheiro de objetos não existir
            f.lerFicheiroTexto(dados);
        } else {
            f.lerFicheiroObjetos(dados);
        }

        JFrame frame = new JFrame();
        frame.setTitle("POOF");
        frame.setSize(500, 500);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        JLabel labelMenu = new JLabel("Menu", SwingConstants.CENTER);
        JButton buttonCriarCliente = new JButton("Criar Cliente");
        JButton buttonEditarCliente = new JButton("Editar Cliente");
        JButton buttonListaCliente = new JButton("Lista Clientes");
        JButton buttonCriarFatura = new JButton("Criar Fatura");
        JButton buttonEditarFatura = new JButton("Editar Fatura");
        JButton buttonListaFatura = new JButton("Lista Faturas");
        JButton buttonVisualizarFatura = new JButton("Visualizar Fatura");
        JButton buttonImportarFaturas = new JButton("Importar Faturas");
        JButton buttonExportarFaturas = new JButton("Exportar Faturas");
        JButton buttonSair = new JButton("Sair");

        JPanel panelMenu = new JPanel();
        panelMenu.setLayout(new GridLayout(11, 1));
        panelMenu.add(labelMenu);
        panelMenu.add(buttonCriarCliente);
        panelMenu.add(buttonEditarCliente);
        panelMenu.add(buttonListaCliente);  // Adiciona o botão de listar clientes
        panelMenu.add(buttonCriarFatura);
        panelMenu.add(buttonEditarFatura);
        panelMenu.add(buttonListaFatura);  // Adiciona o botão de listar faturas
        panelMenu.add(buttonVisualizarFatura);
        panelMenu.add(buttonImportarFaturas);
        panelMenu.add(buttonExportarFaturas);
        panelMenu.add(buttonSair);

        buttonCriarCliente.addActionListener(new ButtonCriarCliente());
        buttonListaCliente.addActionListener(new ButtonListaCliente());  // Adiciona o listener para listar os clientes
        buttonListaFatura.addActionListener(new ButtonListaFatura());  // Adiciona o listener para listar as faturas
        buttonVisualizarFatura.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                mostrarFatura();
            }
        });

        buttonSair.addActionListener(new ButtonSair(f, dados));

        frame.add(panelMenu);

        frame.setVisible(true);
    }

    private class ButtonCriarCliente implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            System.out.println("Criar Cliente");
            criarCliente();
        }
    }

    private class ButtonSair implements ActionListener {
        private Ficheiros f;
        private Dados dados;

        public ButtonSair(Ficheiros f, Dados dados) {
            this.f = f;
            this.dados = dados;
        }

        @Override
        public void actionPerformed(ActionEvent e) {
            System.out.println("Saindo...");
            f.escreverFicheiroObjetos(dados);
            System.exit(0);  // Finaliza a aplicação
        }
    }

    public void criarCliente() {
        JFrame frame = new JFrame();
        frame.setTitle("Criar Cliente");
        frame.setSize(500, 500);
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);

        JLabel labelNome = new JLabel("Nome: ");
        textFieldNome = new JTextField();  // Atribuindo a variável de classe
        JLabel labelNif = new JLabel("NIF: ");
        textFieldNif = new JTextField();  // Atribuindo a variável de classe
        JLabel labelLoc = new JLabel("Localização: ");

        String[] loc = {"Madeira", "Açores", "Portugal Continental"};
        textFieldLoc = new JComboBox<>(loc);  // Atribuindo a variável de classe

        JButton buttonCriar = new JButton("Criar");
        JButton buttonCancelar = new JButton("Cancelar");

        JPanel panelCriarCliente = new JPanel();
        panelCriarCliente.setLayout(new GridLayout(5, 2));
        panelCriarCliente.add(labelNome);
        panelCriarCliente.add(textFieldNome);
        panelCriarCliente.add(labelNif);
        panelCriarCliente.add(textFieldNif);
        panelCriarCliente.add(labelLoc);
        panelCriarCliente.add(textFieldLoc);
        panelCriarCliente.add(buttonCriar);
        panelCriarCliente.add(buttonCancelar);

        buttonCriar.addActionListener(new ButtonCriar());
        buttonCancelar.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                frame.dispose();  // Fecha a janela de criação de cliente
            }
        });

        frame.add(panelCriarCliente);
        frame.setVisible(true);
    }

    private class ButtonCriar implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            String nif = textFieldNif.getText();
            String nome = textFieldNome.getText();
            // Usar getSelectedItem() para pegar o valor selecionado no JComboBox
            String localizacao = (String) textFieldLoc.getSelectedItem();

            // Verifica se já existe um cliente com o mesmo NIF
            for (Cliente cliente : dados.getClientes()) {
                if (nif.equals(cliente.getNif())) {
                    // Se já existir, exibe a mensagem de erro e retorna sem adicionar o cliente
                    JOptionPane.showMessageDialog(null, "Erro: Já existe um cliente com este NIF!", "Erro", JOptionPane.ERROR_MESSAGE);
                    return;
                }
            }

            // Se o NIF não existir, cria e adiciona o novo cliente
            Cliente cliente = new Cliente();
            cliente.setNome(nome);
            cliente.setNif(nif);
            cliente.setLocalizacao(localizacao);
            dados.adicionarCliente(cliente);

            // (Opcional) Mensagem de sucesso
            JOptionPane.showMessageDialog(null, "Cliente criado com sucesso!", "Sucesso", JOptionPane.INFORMATION_MESSAGE);
            textFieldNome.setText("");  // Limpar o campo de nome
            textFieldNif.setText("");   // Limpar o campo de NIF
            textFieldLoc.setSelectedIndex(-1);  // Limpar a seleção do JComboBox
        }
    }

    // Ação para listar os clientes
    private class ButtonListaCliente implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            listarClientes();
        }
    }

    // Método para listar os clientes
    public void listarClientes() {
        // Criando um JFrame para exibir a lista
        JFrame frame = new JFrame();
        frame.setTitle("Lista de Clientes");
        frame.setSize(400, 400);
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);

        // Criando o painel principal com BoxLayout para colocar os itens verticalmente
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));

        // Cabeçalho
        JPanel headerPanel = new JPanel();
        headerPanel.setLayout(new GridLayout(1, 3));  // 3 colunas para Nome, NIF e Localização
        headerPanel.add(new JLabel("Nome"));
        headerPanel.add(new JLabel("NIF"));
        headerPanel.add(new JLabel("Localização"));
        panel.add(headerPanel);

        // Listando os clientes
        for (Cliente cliente : dados.getClientes()) {
            JPanel clientePanel = new JPanel();
            clientePanel.setLayout(new GridLayout(1, 3));  // 3 colunas para cada campo
            clientePanel.add(new JLabel(cliente.getNome()));
            clientePanel.add(new JLabel(cliente.getNif()));
            clientePanel.add(new JLabel(cliente.getLocalizacao()));
            panel.add(clientePanel);
        }

        // Adicionando o painel principal com todos os itens
        JScrollPane scrollPane = new JScrollPane(panel);
        frame.add(scrollPane);

        // Tornando o frame visível
        frame.setVisible(true);
    }

    // Ação para listar as faturas
    private class ButtonListaFatura implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            listarFaturas();
        }
    }

    // Método para listar as faturas
    public void listarFaturas() {
        // Criando um JFrame para exibir a lista de faturas
        JFrame frame = new JFrame();
        frame.setTitle("Lista de Faturas");
        frame.setSize(400, 400);
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);

        // Criando o painel principal com BoxLayout para colocar os itens verticalmente
        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));

        // Cabeçalho
        JPanel headerPanel = new JPanel();
        headerPanel.setLayout(new GridLayout(1, 1));  // Uma única coluna
        headerPanel.add(new JLabel("Informações das Faturas"));
        panel.add(headerPanel);

        // Listando as faturas
        for (Fatura fatura : dados.getFaturas()) {
            // Cria um painel para exibir cada fatura
            JPanel faturaPanel = new JPanel();
            faturaPanel.setLayout(new BorderLayout());

            // Adicionando as informações da fatura com base no método toString
            JTextArea faturaInfo = new JTextArea(fatura.toString());
            faturaInfo.setEditable(false);
            faturaInfo.setWrapStyleWord(true);
            faturaInfo.setLineWrap(true);
            faturaPanel.add(new JScrollPane(faturaInfo), BorderLayout.CENTER);

            panel.add(faturaPanel);
        }

        // Adicionando o painel principal com todos os itens
        JScrollPane scrollPane = new JScrollPane(panel);
        frame.add(scrollPane);

        // Tornando o frame visível
        frame.setVisible(true);
    }

    public void mostrarFatura() {
        // Criando o JFrame para exibir a busca da fatura
        JFrame frame = new JFrame();
        frame.setTitle("Buscar Fatura");
        frame.setSize(400, 200);
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);

        // Criando o painel principal
        JPanel panel = new JPanel();
        panel.setLayout(new GridLayout(3, 1));  // Layout simples com 3 linhas

        // Adicionando componentes
        JLabel label = new JLabel("Digite o número da fatura: ");
        JTextField textFieldNumeroFatura = new JTextField(10);  // Campo de texto para digitar o número da fatura
        JButton buttonBuscar = new JButton("Buscar");

        panel.add(label);
        panel.add(textFieldNumeroFatura);
        panel.add(buttonBuscar);

        frame.add(panel);
        frame.setVisible(true);

        // Adicionando o listener para o botão de buscar
        buttonBuscar.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                String numeroFatura = textFieldNumeroFatura.getText();  // Pegando o número da fatura do campo de texto
                boolean encontrada = false;

                // Verificando se a fatura existe
                for (Fatura fatura : dados.getFaturas()) {
                    if (fatura.getNumeroFatura().equals(numeroFatura)) {
                        // Se encontrada, mostra as informações da fatura
                        JOptionPane.showMessageDialog(null, fatura.toString(), "Fatura Encontrada", JOptionPane.INFORMATION_MESSAGE);
                        encontrada = true;
                        break;
                    }
                }

                // Se a fatura não for encontrada
                if (!encontrada) {
                    JOptionPane.showMessageDialog(null, "Fatura não encontrada!", "Erro", JOptionPane.ERROR_MESSAGE);
                }
            }
        });
    }

}