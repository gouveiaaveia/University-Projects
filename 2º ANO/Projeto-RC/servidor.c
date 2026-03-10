#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <signal.h>
#include "config.h" // Já inclui as novas definições

#define MAX_CLIENTS 3
#define SERVER_TCP_PORT 80 // Alterado para evitar conflito com porta 80 que requer root
#define SECRET_KEY "CHAVE_SEGURA"

// Variáveis Globais
ConfigMessage current_config = {1, 1, 1, 1000, 3}; // Configuração inicial
int client_sockets[MAX_CLIENTS] = {0};
pthread_mutex_t clients_mutex = PTHREAD_MUTEX_INITIALIZER;
int server_running = 1;
int server_fd = -1; // Socket de escuta do servidor TCP
int multicast_send_fd = -1; // Socket para enviar mensagens multicast
struct sockaddr_in multicast_send_addr;


// Função para enviar mensagem de shutdown para todos os clientes (via multicast)
void send_shutdown_to_all_clients() {
    if (multicast_send_fd < 0) {
        fprintf(stderr, "[SERVER_ERROR] Socket multicast de envio não inicializado para shutdown.\n");
        return;
    }

    PowerUDPPacket shutdown_packet; // Usamos PowerUDPPacket para consistência com o cliente
    shutdown_packet.header.type = MSG_TYPE_SERVER_SHUTDOWN;
    shutdown_packet.header.seq_num = 0; // Não relevante para shutdown
    shutdown_packet.header.payload_len = 0; // Não há payload específico para shutdown

    printf("[SERVER] Enviando mensagem de SHUTDOWN via multicast...\n");
    int sent = sendto(multicast_send_fd, &shutdown_packet.header, sizeof(PowerUDPHeader), 0,
                      (struct sockaddr*)&multicast_send_addr, sizeof(multicast_send_addr));
    if (sent < 0) {
        perror("[SERVER_ERROR] Falha ao enviar shutdown multicast");
    } else {
        printf("[SERVER] Mensagem de SHUTDOWN multicast enviada (%d bytes).\n", sent);
    }
}

// Handler para SIGINT (Ctrl+C)
void handle_sigint(int sig) {
    (void)sig;
    printf("\n[SERVER] Encerrando servidor...\n");
    server_running = 0;

    send_shutdown_to_all_clients(); // Notifica clientes via multicast

    // Fecha sockets dos clientes
    pthread_mutex_lock(&clients_mutex);
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (client_sockets[i] != 0) {
            printf("[SERVER] Fechando socket do cliente %d\n", client_sockets[i]);
            close(client_sockets[i]);
            client_sockets[i] = 0;
        }
    }
    pthread_mutex_unlock(&clients_mutex);

    // Fecha socket de escuta do servidor
    if (server_fd != -1) {
        printf("[SERVER] Fechando socket de escuta do servidor TCP.\n");
        close(server_fd);
        server_fd = -1;
    }
    // Fecha socket de envio multicast
    if (multicast_send_fd != -1) {
        printf("[SERVER] Fechando socket de envio multicast.\n");
        close(multicast_send_fd);
        multicast_send_fd = -1;
    }
    exit(0); // Termina o processo
}

// Função para enviar a configuração atual para todos os clientes via multicast
void broadcast_config_to_clients() {
    if (multicast_send_fd < 0) {
        fprintf(stderr, "[SERVER_ERROR] Socket multicast de envio não inicializado.\n");
        return;
    }

    PowerUDPPacket config_packet; // Usamos PowerUDPPacket para consistência com o cliente
    config_packet.header.type = MSG_TYPE_DATA; // Cliente espera config como MSG_TYPE_DATA
    config_packet.header.seq_num = 0; // Sequência não crítica para broadcast de config
    
    pthread_mutex_lock(&clients_mutex); // Protege current_config durante a cópia
    config_packet.header.payload_len = htons(sizeof(ConfigMessage));
    memcpy(config_packet.payload, &current_config, sizeof(ConfigMessage));
    pthread_mutex_unlock(&clients_mutex);

    printf("[SERVER] Enviando nova configuração via multicast...\n");
    int sent = sendto(multicast_send_fd, &config_packet, sizeof(PowerUDPHeader) + sizeof(ConfigMessage), 0,
                      (struct sockaddr*)&multicast_send_addr, sizeof(multicast_send_addr));
    if (sent < 0) {
        perror("[SERVER_ERROR] Falha ao enviar configuração multicast");
    } else {
        printf("[SERVER] Configuração multicast enviada (%d bytes).\n", sent);
    }
}

// Thread para lidar com cada cliente
void* handle_client(void* arg) {
    int client_sock = *(int*)arg;
    free(arg); // Libera a memória alocada para o argumento da thread

    RegisterMessage reg_msg;
    struct sockaddr_in client_addr_info;
    socklen_t addr_len = sizeof(client_addr_info);
    getpeername(client_sock, (struct sockaddr*)&client_addr_info, &addr_len);
    char client_ip_str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &client_addr_info.sin_addr, client_ip_str, INET_ADDRSTRLEN);
    printf("[SERVER] Nova conexão de %s:%d (socket %d)\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);

    // 1. Ler mensagem de registro
    if (recv(client_sock, &reg_msg, sizeof(reg_msg), 0) <= 0) {
        perror("[SERVER_ERROR] Falha ao receber mensagem de registro");
        printf("[SERVER] Cliente %s:%d (socket %d) desconectado antes do registro.\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);
        close(client_sock);
        return NULL;
    }

    // 2. Verifica chave pré-compartilhada
    if (strncmp(reg_msg.psk, SECRET_KEY, sizeof(reg_msg.psk)) != 0) {
        fprintf(stderr, "[SERVER] Registro negado para %s:%d (socket %d): chave PSK inválida.\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);
        send(client_sock, "PSK_FAIL", strlen("PSK_FAIL"), 0); // Informa o cliente
        close(client_sock);
        return NULL;
    }

    // 3. Resposta de sucesso e adicionar à lista de clientes
    if (send(client_sock, "OK", 2, 0) <= 0) {
        perror("[SERVER_ERROR] Falha ao enviar confirmação de registro");
        close(client_sock);
        return NULL;
    }
    
    pthread_mutex_lock(&clients_mutex);
    int added = 0;
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (client_sockets[i] == 0) {
            client_sockets[i] = client_sock;
            added = 1;
            break;
        }
    }
    pthread_mutex_unlock(&clients_mutex);

    if (!added) {
        fprintf(stderr, "[SERVER] Máximo de clientes (%d) atingido. Conexão de %s:%d (socket %d) rejeitada.\n", MAX_CLIENTS, client_ip_str, ntohs(client_addr_info.sin_port), client_sock);
        send(client_sock, "FULL", strlen("FULL"), 0); // Informa o cliente
        close(client_sock);
        return NULL;
    }
    printf("[SERVER] Cliente %s:%d (socket %d) registrado com sucesso.\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);

    // 4. Enviar configuração atual para o novo cliente
    printf("[SERVER] Enviando configuração atual para o cliente %s:%d...\n", client_ip_str, ntohs(client_addr_info.sin_port));
    pthread_mutex_lock(&clients_mutex); // Protege current_config durante a cópia/envio
    if (send(client_sock, &current_config, sizeof(current_config), 0) <= 0) {
        perror("[SERVER_ERROR] Falha ao enviar configuração inicial");
        pthread_mutex_unlock(&clients_mutex);
        // Continua para o loop de tratamento, pode ser desconexão temporária
    } else {
         pthread_mutex_unlock(&clients_mutex);
    }
   

    // 5. Loop para processar pedidos de configuração e desconexão
    ClientServerTCPHeader tcp_header;
    ConfigMessage new_config_request;
    int bytes_received;

    while (server_running) {
        // Ler o cabeçalho TCP
        bytes_received = recv(client_sock, &tcp_header, sizeof(ClientServerTCPHeader), 0);

        if (bytes_received <= 0) {
            if (bytes_received == 0) {
                printf("[SERVER] Cliente %s:%d (socket %d) desconectado (TCP).\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);
            } else {
                perror("[SERVER_ERROR] Erro ao receber cabeçalho TCP do cliente");
            }
            break; // Sai do loop e encerra a thread do cliente
        }

        if (bytes_received == sizeof(ClientServerTCPHeader)) {
            if (tcp_header.message_type == TCP_MSG_TYPE_CONFIG_REQUEST) {
                // Ler o payload da ConfigMessage
                bytes_received = recv(client_sock, &new_config_request, sizeof(ConfigMessage), 0);
                if (bytes_received == sizeof(ConfigMessage)) {
                    printf("[SERVER] Cliente %s:%d solicitou alteração de configuração.\n", client_ip_str, ntohs(client_addr_info.sin_port));
                    
                    pthread_mutex_lock(&clients_mutex);
                    current_config = new_config_request; // Atualiza configuração global
                    pthread_mutex_unlock(&clients_mutex);
                    
                    broadcast_config_to_clients(); // Envia para todos via multicast

                } else if (bytes_received <= 0) {
                    printf("[SERVER] Cliente %s:%d desconectado ao enviar payload de config.\n", client_ip_str, ntohs(client_addr_info.sin_port));
                    break;
                } else {
                     fprintf(stderr, "[SERVER_WARNING] Recebido payload de config com tamanho incorreto (%d bytes) de %s:%d\n", bytes_received, client_ip_str, ntohs(client_addr_info.sin_port));
                }
            } else if (tcp_header.message_type == TCP_MSG_TYPE_DISCONNECT_REQUEST) {
                printf("[SERVER] Cliente %s:%d (socket %d) solicitou desconexão.\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);
                break; // Sai do loop e encerra a thread do cliente
            } else {
                fprintf(stderr, "[SERVER_WARNING] Recebido tipo de mensagem TCP desconhecido (%d) de %s:%d\n", tcp_header.message_type, client_ip_str, ntohs(client_addr_info.sin_port));
            }
        } else {
             fprintf(stderr, "[SERVER_WARNING] Recebido cabeçalho TCP com tamanho incorreto (%d bytes) de %s:%d\n", bytes_received, client_ip_str, ntohs(client_addr_info.sin_port));
        }
    }

    // Remover cliente da lista e fechar socket
    pthread_mutex_lock(&clients_mutex);
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (client_sockets[i] == client_sock) {
            client_sockets[i] = 0;
            break;
        }
    }
    pthread_mutex_unlock(&clients_mutex);
    printf("[SERVER] Encerrando thread para cliente %s:%d (socket %d).\n", client_ip_str, ntohs(client_addr_info.sin_port), client_sock);
    close(client_sock);
    return NULL;
}

int main() {
    struct sockaddr_in address;
    socklen_t addrlen = sizeof(address);

    printf("[SERVER] Iniciando servidor...\n");

    // Configurar handler para SIGINT (Ctrl+C)
    signal(SIGINT, handle_sigint);

    // 1. Criar socket TCP para escuta
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("[SERVER_FATAL] Falha ao criar socket TCP");
        exit(EXIT_FAILURE);
    }
    printf("[SERVER] Socket TCP de escuta criado (fd=%d).\n", server_fd);

    // Permitir reuso do endereço
    int reuse = 1; // 1 para habilitar
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
        perror("[SERVER_FATAL] Falha ao configurar SO_REUSEADDR");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(SERVER_TCP_PORT);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("[SERVER_FATAL] Falha no bind do socket TCP");
        close(server_fd);
        exit(EXIT_FAILURE);
    }
    printf("[SERVER] Socket TCP bind na porta %d.\n", SERVER_TCP_PORT);

    if (listen(server_fd, MAX_CLIENTS) < 0) {
        perror("[SERVER_FATAL] Falha no listen do socket TCP");
        close(server_fd);
        exit(EXIT_FAILURE);
    }

    // 2. Configurar socket Multicast para envio
    multicast_send_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (multicast_send_fd < 0) {
        perror("[SERVER_FATAL] Falha ao criar socket multicast de envio");
        close(server_fd);
        exit(EXIT_FAILURE);
    }
    printf("[SERVER] Socket multicast de envio criado (fd=%d).\n", multicast_send_fd);

    memset(&multicast_send_addr, 0, sizeof(multicast_send_addr));
    multicast_send_addr.sin_family = AF_INET;
    multicast_send_addr.sin_port = htons(MULTICAST_PORT);
    if (inet_pton(AF_INET, MULTICAST_GROUP, &multicast_send_addr.sin_addr) <= 0) {
        perror("[SERVER_FATAL] Falha ao converter endereço IP multicast");
        close(server_fd);
        close(multicast_send_fd);
        exit(EXIT_FAILURE);
    }

    // Configurar TTL para multicast (opcional, mas bom para redes de teste)
    int multicast_ttl = 10;
    if (setsockopt(multicast_send_fd, IPPROTO_IP, IP_MULTICAST_TTL, &multicast_ttl, sizeof(multicast_ttl)) < 0) {
        perror("[SERVER_WARNING] Falha ao configurar TTL multicast");
        // Não é fatal, pode continuar.
    }
    printf("[SERVER] Socket multicast configurado para %s:%d com TTL %d.\n", MULTICAST_GROUP, MULTICAST_PORT, multicast_ttl);


    printf("[SERVER] Aguardando conexões na porta %d...\n", SERVER_TCP_PORT);

    while (server_running) {
        int new_socket_ptr_val = accept(server_fd, (struct sockaddr*)&address, &addrlen);
        if (new_socket_ptr_val < 0) {
            if (server_running) { // Evita erro se accept for interrompido por SIGINT
                 perror("[SERVER_WARNING] Falha no accept TCP");
            }
            continue;
        }

        // Criar thread para cliente
        int* new_sock_ptr = malloc(sizeof(int));
        if (!new_sock_ptr) {
            perror("[SERVER_FATAL] Falha ao alocar memória para socket do cliente");
            close(new_socket_ptr_val);
            continue;
        }
        *new_sock_ptr = new_socket_ptr_val;
        
        pthread_t tid;
        if (pthread_create(&tid, NULL, handle_client, new_sock_ptr) != 0) {
            perror("[SERVER_ERROR] Falha ao criar thread para cliente");
            free(new_sock_ptr);
            close(new_socket_ptr_val);
        } else {
            pthread_detach(tid); // Não precisamos esperar por esta thread
        }
    }

    printf("[SERVER] Loop principal encerrado.\n");
    // A limpeza de sockets de cliente e globais é feita no handle_sigint
    return 0;
}