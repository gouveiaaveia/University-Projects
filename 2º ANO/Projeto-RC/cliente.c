#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <time.h>
#include <math.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#include <sys/time.h>
#include "config.h"

int tcp_fd = -1;
int udp_fd = -1;
int multicast_fd = -1;
struct sockaddr_in server_addr_tcp;
struct ip_mreq mreq_join;
ConfigMessage current_config = {1, 1, 1, 1000, 3}; // Configuração padrão
uint16_t next_seq_num_udp = 0; // Número de sequência para pacotes de DADOS enviados

char message_queue[MAX_QUEUE][1024];
int message_sizes[MAX_QUEUE];
int queue_head = 0, queue_tail = 0;
pthread_mutex_t queue_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_t receiver_thread_id = 0;
pthread_t display_thread_id = 0;

void close_protocol_internal(int initiated_by_server_shutdown);

struct {
    int retransmissions;
    int delivery_time_ms;
} last_stats;

int packet_loss_probability = 0;

volatile sig_atomic_t client_keep_running = 1;

typedef enum {
    ACK_STATUS_PENDING,
    ACK_STATUS_ACK_RECEIVED,
    ACK_STATUS_NACK_RECEIVED,
    ACK_STATUS_TIMEOUT_INTERNAL
} AckStatusType;

typedef struct {
    uint16_t seq_num_expected;
    struct sockaddr_in expected_sender_addr;
    volatile AckStatusType status;
    pthread_cond_t cond_var;
    pthread_mutex_t mutex;
    int in_use;
    pthread_t waiting_thread_id;
} AckWaitEntry;

#define MAX_CONCURRENT_SENDS 5
AckWaitEntry ack_wait_pool[MAX_CONCURRENT_SENDS];
pthread_mutex_t ack_pool_access_mutex = PTHREAD_MUTEX_INITIALIZER;

typedef struct {
    struct sockaddr_in peer_addr;
    uint16_t last_seq_num_processed;
    time_t last_communication_time;
    int in_use;
} PeerSequenceState;

#define MAX_PEERS 10
PeerSequenceState peer_seq_state_pool[MAX_PEERS];
pthread_mutex_t peer_seq_pool_mutex = PTHREAD_MUTEX_INITIALIZER;


// Funções auxiliares
int receive_message(char* buffer, int bufsize);
unsigned int calculate_timeout(int attempt, uint16_t base_timeout);
void create_ack_packet_udp(PowerUDPPacket* pkt, uint16_t seq_num, uint8_t type);


void initialize_ack_wait_pool() {
    for (int i = 0; i < MAX_CONCURRENT_SENDS; i++) {
        ack_wait_pool[i].in_use = 0;
        ack_wait_pool[i].seq_num_expected = 0;
        ack_wait_pool[i].waiting_thread_id = 0;
        ack_wait_pool[i].status = ACK_STATUS_PENDING;
        if (pthread_mutex_init(&ack_wait_pool[i].mutex, NULL) != 0) {
            perror("[FATAL_CLIENT] Falha ao inicializar mutex para ack_wait_pool");
        }
        if (pthread_cond_init(&ack_wait_pool[i].cond_var, NULL) != 0) {
            perror("[FATAL_CLIENT] Falha ao inicializar cond_var para ack_wait_pool");
        }
    }
}

void destroy_ack_wait_pool() {
    for (int i = 0; i < MAX_CONCURRENT_SENDS; i++) {
        pthread_mutex_destroy(&ack_wait_pool[i].mutex);
        pthread_cond_destroy(&ack_wait_pool[i].cond_var);
    }
}

void initialize_peer_seq_state_pool() {
    pthread_mutex_lock(&peer_seq_pool_mutex);
    for (int i = 0; i < MAX_PEERS; i++) {
        peer_seq_state_pool[i].in_use = 0;
        peer_seq_state_pool[i].last_seq_num_processed = 0;
    }
    pthread_mutex_unlock(&peer_seq_pool_mutex);
}


// Thread para exibir mensagens da fila
void* display_loop(void* arg) {
    (void)arg;
    char rx_buffer[1024];
    pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
    pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL); 

    printf("[CLIENT_DISPLAY] Display thread iniciada.\n");
    while (client_keep_running) { // Usa a flag global
        int size = receive_message(rx_buffer, sizeof(rx_buffer));
        if (size > 0) {
            printf("\n< Mensagem Recebida: %.*s\n", size, rx_buffer);
            printf("Digite comando ou <destino> <mensagem> (ou 'exit'): "); 
            fflush(stdout);
        }
        usleep(100000); 
    }
    printf("[CLIENT_DISPLAY] Display thread terminando.\n");
    return NULL;
}


// Thread para receber mensagens UDP e multicast
void* receiver_loop(void* arg) {
    (void)arg;
    fd_set read_fds;
    struct timeval select_timeout;
    
    pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
    pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL); 

    printf("[CLIENT_RCV_LOOP] Receiver thread (UDP/Multicast) iniciada.\n");

    while (client_keep_running) {
        FD_ZERO(&read_fds);
        int max_fd = -1;

        if (udp_fd >= 0) {
            FD_SET(udp_fd, &read_fds);
            if (udp_fd > max_fd) max_fd = udp_fd;
        }
        if (multicast_fd >= 0) {
            FD_SET(multicast_fd, &read_fds);
            if (multicast_fd > max_fd) max_fd = multicast_fd;
        }
        
        if (max_fd < 0) {
             if (client_keep_running) printf("[CLIENT_RCV_LOOP] Sockets UDP e Multicast não estão ativos. Encerrando loop.\n");
             break;
        }

        select_timeout.tv_sec = 1;
        select_timeout.tv_usec = 0;

        int activity = select(max_fd + 1, &read_fds, NULL, NULL, &select_timeout);

        if (!client_keep_running) break; // Verifica novamente após select

        if (activity < 0) {
            if (errno == EINTR && client_keep_running) continue;
            if (client_keep_running) perror("[CLIENT_RCV_LOOP] Erro no select");
            break;
        }
        if (activity == 0) continue;

        // Processar mensagens UDP normais (dados de outros clientes, ACKs, NACKs)
        if (udp_fd >=0 && FD_ISSET(udp_fd, &read_fds)) {
            PowerUDPPacket packet;
            struct sockaddr_in sender_addr_udp;
            socklen_t addr_len_udp = sizeof(sender_addr_udp);

            int bytes = recvfrom(udp_fd, &packet, sizeof(packet), 0,
                                (struct sockaddr*)&sender_addr_udp, &addr_len_udp);

            if (bytes > 0) {
                char sender_ip_str[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &sender_addr_udp.sin_addr, sender_ip_str, sizeof(sender_ip_str));
                uint16_t received_seq_num_udp = ntohs(packet.header.seq_num);

                if (packet.header.type == MSG_TYPE_DATA) {
                    // Simular perda de pacote (APENAS PARA DADOS RECEBIDOS)
                    if (packet_loss_probability > 0 && (rand() % 100 < packet_loss_probability)) {
                        printf("[CLIENT_RCV_LOOP] Pacote de DADOS de %s:%d (seq=%u) perdido (simulado)\n",
                               sender_ip_str, ntohs(sender_addr_udp.sin_port), received_seq_num_udp);
                        continue;
                    }
                    
                    // --- Verificação de Sequência por Emissor ---
                    int process_packet = 1;
                    if (current_config.enable_sequence) {
                        pthread_mutex_lock(&peer_seq_pool_mutex);
                        int peer_idx = -1;
                        for (int i = 0; i < MAX_PEERS; i++) {
                            if (peer_seq_state_pool[i].in_use &&
                                peer_seq_state_pool[i].peer_addr.sin_addr.s_addr == sender_addr_udp.sin_addr.s_addr &&
                                peer_seq_state_pool[i].peer_addr.sin_port == sender_addr_udp.sin_port) {
                                peer_idx = i;
                                break;
                            }
                        }

                        if (peer_idx != -1) { 
                            if (received_seq_num_udp != 0 && received_seq_num_udp <= peer_seq_state_pool[peer_idx].last_seq_num_processed) {
                                printf("[CLIENT_RCV_LOOP] Pacote DADOS de %s:%d (seq recvd %u, last proc %u) FORA DE ORDEM/REPETIDO. Enviando NACK.\n",
                                       sender_ip_str, ntohs(sender_addr_udp.sin_port), received_seq_num_udp, peer_seq_state_pool[peer_idx].last_seq_num_processed);
                                PowerUDPPacket nack_pkt;
                                create_ack_packet_udp(&nack_pkt, received_seq_num_udp, MSG_TYPE_NACK);
                                sendto(udp_fd, &nack_pkt.header, sizeof(PowerUDPHeader), 0, (struct sockaddr*)&sender_addr_udp, addr_len_udp);
                                process_packet = 0; // Não processar este pacote
                            } else {
                                peer_seq_state_pool[peer_idx].last_seq_num_processed = received_seq_num_udp;
                                peer_seq_state_pool[peer_idx].last_communication_time = time(NULL);
                            }
                        } else { // Novo peer
                            int new_peer_idx = -1;
                            for (int i = 0; i < MAX_PEERS; i++) { // Encontra slot livre
                                if (!peer_seq_state_pool[i].in_use) {
                                    new_peer_idx = i;
                                    break;
                                }
                            }
                            // TODO: Política de substituição LRU se MAX_PEERS for atingido. Por agora, ignora se cheio.
                            if (new_peer_idx != -1) {
                                peer_seq_state_pool[new_peer_idx].in_use = 1;
                                peer_seq_state_pool[new_peer_idx].peer_addr = sender_addr_udp;
                                peer_seq_state_pool[new_peer_idx].last_seq_num_processed = received_seq_num_udp;
                                peer_seq_state_pool[new_peer_idx].last_communication_time = time(NULL);
                                printf("[CLIENT_RCV_LOOP] Novo peer %s:%d adicionado para rastreamento de sequência (seq=%u).\n",
                                       sender_ip_str, ntohs(sender_addr_udp.sin_port), received_seq_num_udp);
                            } else {
                                printf("[CLIENT_RCV_LOOP_WARN] Máximo de peers para rastreamento de sequência atingido. Não rastreando %s:%d.\n",
                                       sender_ip_str, ntohs(sender_addr_udp.sin_port));
                                // Sem rastreamento, não podemos validar sequência, mas ainda podemos aceitar.
                            }
                        }
                        pthread_mutex_unlock(&peer_seq_pool_mutex);
                    }
                    // --- Fim Verificação de Sequência ---

                    if (process_packet) {
                        PowerUDPPacket ack_pkt;
                        create_ack_packet_udp(&ack_pkt, received_seq_num_udp, MSG_TYPE_ACK);
                        if (sendto(udp_fd, &ack_pkt.header, sizeof(PowerUDPHeader), 0, (struct sockaddr*)&sender_addr_udp, addr_len_udp) < 0) {
                            perror("[CLIENT_RCV_LOOP] Erro ao enviar ACK");
                        } else {
                             printf("[CLIENT_RCV_LOOP] ACK enviado para %s:%d (para dados seq=%u)\n", sender_ip_str, ntohs(sender_addr_udp.sin_port), received_seq_num_udp);
                        }
                        
                        uint16_t payload_size = ntohs(packet.header.payload_len);
                        if (payload_size > sizeof(packet.payload)) payload_size = sizeof(packet.payload);

                        pthread_mutex_lock(&queue_mutex);
                        if ((queue_tail + 1) % MAX_QUEUE != queue_head) {
                            memcpy(message_queue[queue_tail], packet.payload, payload_size);
                            message_sizes[queue_tail] = payload_size;
                            queue_tail = (queue_tail + 1) % MAX_QUEUE;
                        } else {
                            fprintf(stderr, "[CLIENT_RCV_LOOP] Fila de mensagens cheia. Pacote de DADOS (seq %u) descartado.\n", received_seq_num_udp);
                        }
                        pthread_mutex_unlock(&queue_mutex);
                    }

                } else if (packet.header.type == MSG_TYPE_ACK || packet.header.type == MSG_TYPE_NACK) {
                    printf("[CLIENT_RCV_LOOP] Recebido %s de %s:%d para seq=%u\n",
                           (packet.header.type == MSG_TYPE_ACK ? "ACK" : "NACK"),
                           sender_ip_str, ntohs(sender_addr_udp.sin_port), received_seq_num_udp);

                    pthread_mutex_lock(&ack_pool_access_mutex);
                    for (int i = 0; i < MAX_CONCURRENT_SENDS; i++) {
                        if (ack_wait_pool[i].in_use && ack_wait_pool[i].seq_num_expected == received_seq_num_udp &&
                            ack_wait_pool[i].expected_sender_addr.sin_addr.s_addr == sender_addr_udp.sin_addr.s_addr &&
                            ack_wait_pool[i].expected_sender_addr.sin_port == sender_addr_udp.sin_port) {
                            
                            pthread_mutex_lock(&ack_wait_pool[i].mutex);
                            if (ack_wait_pool[i].status == ACK_STATUS_PENDING) { // Só atualiza se ainda estiver pendente
                                ack_wait_pool[i].status = (packet.header.type == MSG_TYPE_ACK) ? ACK_STATUS_ACK_RECEIVED : ACK_STATUS_NACK_RECEIVED;
                                pthread_cond_signal(&ack_wait_pool[i].cond_var);
                                printf("[CLIENT_RCV_LOOP] Sinalizado send_message para ACK/NACK (seq=%u).\n", received_seq_num_udp);
                            }
                            pthread_mutex_unlock(&ack_wait_pool[i].mutex);
                            break; 
                        }
                    }
                    pthread_mutex_unlock(&ack_pool_access_mutex);
                }
            } else if (bytes < 0 && client_keep_running) {
                if (errno != EAGAIN && errno != EWOULDBLOCK) {
                    perror("[CLIENT_RCV_LOOP] Erro no recvfrom UDP");
                }
            }
        } // Fim if (FD_ISSET(udp_fd...

        // Processar multicast
        if (multicast_fd >=0 && FD_ISSET(multicast_fd, &read_fds)) {
            PowerUDPPacket multicast_packet;
            struct sockaddr_in sender_addr_multicast;
            socklen_t addr_len_multicast = sizeof(sender_addr_multicast);
            int bytes = recvfrom(multicast_fd, &multicast_packet, sizeof(multicast_packet), 0,
                                (struct sockaddr*)&sender_addr_multicast, &addr_len_multicast);
            
            if (bytes > 0) {
                // (Lógica de tratamento de multicast como antes)
                 if (multicast_packet.header.type == MSG_TYPE_SERVER_SHUTDOWN) {
                    printf("\n[CLIENT_INFO] Servidor está encerrando. Desconectando...\n");
                    client_keep_running = 0; // Sinaliza para todas as threads terminarem
                    close_protocol_internal(1); 
                    printf("Pressione Enter para finalizar o cliente.\n"); fflush(stdout);
                } else if (multicast_packet.header.type == MSG_TYPE_DATA &&
                           (size_t)bytes >= (sizeof(PowerUDPHeader) + sizeof(ConfigMessage))) {
                    ConfigMessage new_conf; // ... (copia e atualiza config)
                    memcpy(&new_conf, multicast_packet.payload, sizeof(ConfigMessage));
                    current_config = new_conf;
                     printf("\n[CLIENT_INFO] Nova configuração recebida via multicast:\n"); // ... (imprime)
                    printf("  - Retransmissão: %s\n", current_config.enable_retransmission ? "Ativada" : "Desativada");
                    printf("  - Backoff: %s\n", current_config.enable_backoff ? "Ativado" : "Desativado");
                    printf("  - Sequenciamento: %s\n", current_config.enable_sequence ? "Ativado" : "Desativado");
                    printf("  - Timeout base: %u ms\n", current_config.base_timeout);
                    printf("  - Máximo de tentativas: %u\n", current_config.max_retries);
                    printf("Digite comando ou <destino> <mensagem> (ou 'exit'): "); fflush(stdout);
                }
            } else if (bytes < 0 && client_keep_running) {
                 perror("[CLIENT_RCV_LOOP] Erro no recvfrom multicast");
            }
        } // Fim if (FD_ISSET(multicast_fd...

    } // Fim while(client_keep_running)
    printf("[CLIENT_RCV_LOOP] Receiver thread (UDP/Multicast) terminando.\n");
    return NULL;
}


int init_protocol(const char* server_ip, int server_tcp_port, const char* psk) {
    
    initialize_ack_wait_pool();
    initialize_peer_seq_state_pool();

    memset(&server_addr_tcp, 0, sizeof(server_addr_tcp));
    server_addr_tcp.sin_family = AF_INET;
    server_addr_tcp.sin_port = htons(server_tcp_port);
    if (inet_pton(AF_INET, server_ip, &server_addr_tcp.sin_addr) <= 0) {
        perror("[CLIENT_INIT] Endereço IP do servidor inválido");
        return -1;
    }

    // Socket TCP para registro
    tcp_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_fd < 0) {
        perror("[CLIENT_INIT] Falha na criação do socket TCP");
        return -1;
    }

    printf("[CLIENT_INIT] Conectando ao servidor %s:%d via TCP...\n", server_ip, server_tcp_port);
    if (connect(tcp_fd, (struct sockaddr*)&server_addr_tcp, sizeof(server_addr_tcp)) < 0) {
        perror("[CLIENT_INIT] Falha na conexão TCP com o servidor");
        close(tcp_fd); tcp_fd = -1;
        return -1;
    }
    printf("[CLIENT_INIT] Conectado ao servidor via TCP.\n");

    // Enviar registro
    RegisterMessage reg_msg_payload = {0};
    strncpy(reg_msg_payload.psk, psk, sizeof(reg_msg_payload.psk) - 1);
    if (send(tcp_fd, &reg_msg_payload, sizeof(reg_msg_payload), 0) <= 0) {
        perror("[CLIENT_INIT] Falha no envio do registro TCP");
        close(tcp_fd); tcp_fd = -1;
        return -1;
    }
    printf("[CLIENT_INIT] Mensagem de registro enviada.\n");

    // Ler confirmação do servidor
    char server_response_buffer[32];
    int bytes_recv = recv(tcp_fd, server_response_buffer, sizeof(server_response_buffer) - 1, 0);
    if (bytes_recv <= 0) {
        perror("[CLIENT_INIT] Falha ao ler confirmação de registro do servidor");
        close(tcp_fd); tcp_fd = -1;
        return -1;
    }
    server_response_buffer[bytes_recv] = '\0';

    if (strcmp(server_response_buffer, "OK") != 0) {
        fprintf(stderr, "[CLIENT_INIT] Registro rejeitado pelo servidor: %s\n", server_response_buffer);
        close(tcp_fd); tcp_fd = -1;
        return -1;
    }
    printf("[CLIENT_INIT] Registro aceito pelo servidor.\n");

    // Receber configuração inicial do servidor
    if (recv(tcp_fd, &current_config, sizeof(current_config), 0) <= 0) {
        perror("[CLIENT_INIT] Falha ao receber configuração inicial do servidor");
        close(tcp_fd); tcp_fd = -1;
        return -1;
    }
    printf("[CLIENT_INIT] Configuração inicial recebida do servidor:\n");
    printf("  - Retransmissão: %s\n", current_config.enable_retransmission ? "Ativada" : "Desativada");
    printf("  - Backoff: %s\n", current_config.enable_backoff ? "Ativado" : "Desativado");
    printf("  - Sequenciamento: %s\n", current_config.enable_sequence ? "Ativado" : "Desativado");
    printf("  - Timeout base: %u ms\n", current_config.base_timeout);
    printf("  - Máximo de tentativas: %u\n", current_config.max_retries);


    // Criar socket UDP para PowerUDP
    udp_fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (udp_fd < 0) {
        perror("[CLIENT_INIT] Falha na criação do socket UDP");
        close(tcp_fd); tcp_fd = -1;
        return -1;
    }
    struct sockaddr_in local_udp_addr = {0};
    local_udp_addr.sin_family = AF_INET;
    local_udp_addr.sin_port = htons(9000); 
    local_udp_addr.sin_addr.s_addr = INADDR_ANY;
    if (bind(udp_fd, (struct sockaddr*)&local_udp_addr, sizeof(local_udp_addr)) < 0) {
        perror("[CLIENT_INIT] Falha no bind do socket UDP na porta 9000");
        close(udp_fd); udp_fd = -1; close(tcp_fd); tcp_fd = -1; return -1;
    }
    printf("[CLIENT_INIT] Socket UDP bind na porta %d.\n", ntohs(local_udp_addr.sin_port));

    multicast_fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (multicast_fd < 0) {
        perror("[CLIENT_INIT] Falha na criação do socket multicast");
        if (udp_fd >=0) close(udp_fd); if (tcp_fd >=0) close(tcp_fd); return -1;
    }

    int reuse_mcast = 1;

    if (setsockopt(multicast_fd, SOL_SOCKET, SO_REUSEADDR, &reuse_mcast, sizeof(reuse_mcast)) < 0) {
        perror("[CLIENT_INIT] Falha ao configurar SO_REUSEADDR para multicast");
        if (multicast_fd >=0) close(multicast_fd); if (udp_fd >=0) close(udp_fd); if (tcp_fd >=0) close(tcp_fd); return -1;
    }

    struct sockaddr_in local_multicast_bind_addr = {0};
    local_multicast_bind_addr.sin_family = AF_INET;
    local_multicast_bind_addr.sin_port = htons(MULTICAST_PORT);
    local_multicast_bind_addr.sin_addr.s_addr = INADDR_ANY; 

    if (bind(multicast_fd, (struct sockaddr*)&local_multicast_bind_addr, sizeof(local_multicast_bind_addr)) < 0) {
        char err_msg[100]; sprintf(err_msg, "[CLIENT_INIT] Falha no bind do socket multicast na porta %d", MULTICAST_PORT); perror(err_msg);
        if (multicast_fd >=0){
            close(multicast_fd);
        } 
        if (udp_fd >=0){ 
            close(udp_fd); 
        }    
        if (tcp_fd >=0){
             close(tcp_fd); 
        }     
        return -1;
    }
    memset(&mreq_join, 0, sizeof(mreq_join));
    if (inet_pton(AF_INET, MULTICAST_GROUP, &mreq_join.imr_multiaddr.s_addr) <= 0) {
         perror("[CLIENT_INIT] Endereço IP do grupo multicast inválido");
        if (multicast_fd >=0) close(multicast_fd); if (udp_fd >=0) close(udp_fd); if (tcp_fd >=0) close(tcp_fd); return -1;
    }
    mreq_join.imr_interface.s_addr = INADDR_ANY; 
    if (setsockopt(multicast_fd, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq_join, sizeof(mreq_join)) < 0) {
        perror("[CLIENT_INIT] Falha no IP_ADD_MEMBERSHIP para grupo multicast");
        if (multicast_fd >=0) close(multicast_fd); if (udp_fd >=0) close(udp_fd); if (tcp_fd >=0) close(tcp_fd); return -1;
    }
    printf("[CLIENT_INIT] Join no grupo multicast %s realizado com sucesso.\n", MULTICAST_GROUP);

    if (pthread_create(&receiver_thread_id, NULL, receiver_loop, NULL) != 0) {
        perror("[CLIENT_INIT] Falha na criação da thread receptora");
        if (multicast_fd >=0) {setsockopt(multicast_fd, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq_join, sizeof(mreq_join)); close(multicast_fd);}
        if (udp_fd >=0) close(udp_fd); if (tcp_fd >=0) close(tcp_fd); return -1;
    }
    if (pthread_create(&display_thread_id, NULL, display_loop, NULL) != 0) {
        perror("[CLIENT_INIT] Falha na criação da thread de display");
        if (receiver_thread_id != 0) { pthread_cancel(receiver_thread_id); pthread_join(receiver_thread_id, NULL); }
        if (multicast_fd >=0) {setsockopt(multicast_fd, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq_join, sizeof(mreq_join)); close(multicast_fd);}
        if (udp_fd >=0) close(udp_fd); if (tcp_fd >=0) close(tcp_fd); return -1;
    }
    printf("[CLIENT_INIT] Protocolo inicializado com sucesso.\n");
    return 0;
}

void close_protocol_internal(int initiated_by_server_shutdown) {
    printf("[CLIENT_CLOSE] Iniciando fechamento do protocolo (iniciado por %s)...\n", initiated_by_server_shutdown ? "servidor" : "cliente");
    client_keep_running = 0; // Sinaliza para todas as threads terminarem

    // Cancela e junta threads
    if (receiver_thread_id != 0) {
        printf("[CLIENT_CLOSE] Cancelando thread receptora...\n");
        pthread_cancel(receiver_thread_id); // Envia pedido de cancelamento
    }
    if (display_thread_id != 0) {
        printf("[CLIENT_CLOSE] Cancelando thread de display...\n");
        pthread_cancel(display_thread_id);
    }

    // Espera que as threads terminem
    if (receiver_thread_id != 0) {
        pthread_join(receiver_thread_id, NULL);
        receiver_thread_id = 0; 
        printf("[CLIENT_CLOSE] Thread receptora finalizada.\n");
    }
     if (display_thread_id != 0) {
        pthread_join(display_thread_id, NULL);
        display_thread_id = 0;
        printf("[CLIENT_CLOSE] Thread de display finalizada.\n");
    }

    if (!initiated_by_server_shutdown && tcp_fd >= 0) {
        ClientServerTCPHeader disconnect_hdr;
        disconnect_hdr.message_type = TCP_MSG_TYPE_DISCONNECT_REQUEST;
        printf("[CLIENT_CLOSE] Enviando pedido de desconexão TCP para o servidor...\n");
        send(tcp_fd, &disconnect_hdr, sizeof(disconnect_hdr), 0);
    }

    if (multicast_fd >= 0) {
        setsockopt(multicast_fd, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq_join, sizeof(mreq_join));
        close(multicast_fd); multicast_fd = -1; printf("[CLIENT_CLOSE] Socket multicast fechado.\n");
    }

    if (tcp_fd >= 0) { close(tcp_fd); tcp_fd = -1; printf("[CLIENT_CLOSE] Socket TCP fechado.\n");}
    if (udp_fd >= 0) { close(udp_fd); udp_fd = -1; printf("[CLIENT_CLOSE] Socket UDP fechado.\n");}
    
    destroy_ack_wait_pool();
    printf("[CLIENT_CLOSE] Protocolo encerrado.\n");
}

int send_message(const char* destination_str, const char* message, int len) {
    if (udp_fd < 0) {
        fprintf(stderr, "[CLIENT_SEND_MSG] Socket UDP não inicializado.\n");
        return -1;
    }
    if (!client_keep_running) {
        fprintf(stderr, "[CLIENT_SEND_MSG] Cliente não está em execução, mensagem não enviada.\n");
        return -1;
    }

    struct sockaddr_in dest_addr = {0}; // Endereço de destino do pacote UDP
    dest_addr.sin_family = AF_INET;
    char ip_only[64];
    int port_num = 9000;
    
    // Parse <ip>:<porta> ou <ip> (default porta 9000)
    const char* colon_ptr = strchr(destination_str, ':');
    if (colon_ptr != NULL) {
        size_t ip_len = colon_ptr - destination_str;
        if (ip_len < sizeof(ip_only)) {
            strncpy(ip_only, destination_str, ip_len);
            ip_only[ip_len] = '\0';
            port_num = atoi(colon_ptr + 1);
            if (port_num <= 0 || port_num > 65535) port_num = 9000;
        } else {
            strncpy(ip_only, destination_str, sizeof(ip_only)-1); ip_only[sizeof(ip_only)-1] = '\0';
        }
    } else {
        strncpy(ip_only, destination_str, sizeof(ip_only)-1); ip_only[sizeof(ip_only)-1] = '\0';
    }
    if (inet_pton(AF_INET, ip_only, &dest_addr.sin_addr) <= 0) {
        perror("[CLIENT_SEND_MSG] Endereço IP de destino inválido"); return -1;
    }
    dest_addr.sin_port = htons(port_num);

    PowerUDPPacket packet_to_send;
    memset(&packet_to_send, 0, sizeof(PowerUDPPacket));
    uint16_t current_seq_num = next_seq_num_udp++; // Pega o próximo número de sequência
    packet_to_send.header.seq_num = htons(current_seq_num);
    packet_to_send.header.type = MSG_TYPE_DATA;
    if (len > (int)sizeof(packet_to_send.payload)) len = sizeof(packet_to_send.payload);
    packet_to_send.header.payload_len = htons((uint16_t)len);
    memcpy(packet_to_send.payload, message, len);
    size_t packet_total_len = sizeof(PowerUDPHeader) + len;

    last_stats.retransmissions = 0;
    clock_t send_start_time = clock();

    if (!current_config.enable_retransmission) {
        // Sem retransmissão, apenas envia
        if (packet_loss_probability > 0 && (rand() % 100 < packet_loss_probability)) {
            printf("[CLIENT_SEND_MSG] Pacote (seq=%u) para %s:%d perdido (simulado, sem retrans).\n", current_seq_num, ip_only, port_num);
            return 0; 
        }
        if (sendto(udp_fd, &packet_to_send, packet_total_len, 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr)) < 0) {
            perror("[CLIENT_SEND_MSG] Erro ao enviar pacote UDP (sem retrans)"); return -1;
        }
        printf("[CLIENT_SEND_MSG] Pacote (seq=%u) enviado para %s:%d (sem retrans).\n", current_seq_num, ip_only, port_num);
        last_stats.delivery_time_ms = (clock() - send_start_time) * 1000 / CLOCKS_PER_SEC;
        return 0;
    }

    // Com retransmissão
    int ack_wait_idx = -1;
    pthread_mutex_lock(&ack_pool_access_mutex);
    for (int i = 0; i < MAX_CONCURRENT_SENDS; i++) {
        if (!ack_wait_pool[i].in_use) {
            ack_wait_idx = i;
            ack_wait_pool[i].in_use = 1;
            ack_wait_pool[i].seq_num_expected = current_seq_num;
            ack_wait_pool[i].expected_sender_addr = dest_addr; // Espera ACK/NACK deste destino
            ack_wait_pool[i].status = ACK_STATUS_PENDING;
            ack_wait_pool[i].waiting_thread_id = pthread_self();
            break;
        }
    }
    pthread_mutex_unlock(&ack_pool_access_mutex);

    if (ack_wait_idx == -1) {
        fprintf(stderr, "[CLIENT_SEND_MSG] Sem slots de espera por ACK disponíveis. Tente mais tarde.\n");
        // Decrementar next_seq_num_udp? Ou considerar que este seq_num foi "gasto".
        // Para simplificar, não decrementamos, mas a mensagem não é enviada.
        return -1;
    }

    int success = 0;
    for (int attempt = 0; attempt <= current_config.max_retries; attempt++) {
        if (!client_keep_running) { // Verifica se o cliente foi instruído a parar
             success = -1; // Marcar como falha
             break;
        }
        // Simular perda ANTES de enviar
        if (attempt > 0 && packet_loss_probability > 0 && (rand() % 100 < packet_loss_probability)) {
             printf("[CLIENT_SEND_MSG] Pacote (seq=%u, tent. %d) para %s:%d perdido na transmissão (simulado).\n",
                   current_seq_num, attempt, ip_only, port_num);
             // Não envia, vai direto para a espera do timeout (que ocorrerá)
        } else {
            printf("[CLIENT_SEND_MSG] Enviando pacote (seq=%u, tent. %d) para %s:%d\n",
                   current_seq_num, attempt, ip_only, port_num);
            if (sendto(udp_fd, &packet_to_send, packet_total_len, 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr)) < 0) {
                perror("[CLIENT_SEND_MSG] Erro ao enviar pacote UDP na tentativa");
                // Considerar se deve continuar ou falhar imediatamente. Por agora, continua para timeout.
            }
        }

        unsigned int timeout_ms = current_config.enable_backoff ?
            calculate_timeout(attempt, current_config.base_timeout) :
            current_config.base_timeout;

        struct timespec abs_timeout;
        struct timeval now_tv;
        gettimeofday(&now_tv, NULL);
        abs_timeout.tv_sec = now_tv.tv_sec + timeout_ms / 1000;
        abs_timeout.tv_nsec = (now_tv.tv_usec * 1000) + ((timeout_ms % 1000) * 1000000);
        if (abs_timeout.tv_nsec >= 1000000000) {
            abs_timeout.tv_sec++;
            abs_timeout.tv_nsec -= 1000000000;
        }
        
        pthread_mutex_lock(&ack_wait_pool[ack_wait_idx].mutex);
        ack_wait_pool[ack_wait_idx].status = ACK_STATUS_PENDING;

        int wait_ret = 0;
        while (ack_wait_pool[ack_wait_idx].status == ACK_STATUS_PENDING && client_keep_running) {
            wait_ret = pthread_cond_timedwait(&ack_wait_pool[ack_wait_idx].cond_var,
                                              &ack_wait_pool[ack_wait_idx].mutex,
                                              &abs_timeout);
            if (wait_ret == ETIMEDOUT) {
                break;
            } else if (wait_ret != 0 && ack_wait_pool[ack_wait_idx].status == ACK_STATUS_PENDING) {
                // Erro inesperado em timedwait, ou sinal espúrio sem mudança de status
                // Para segurança, considerar como timeout para esta tentativa.
                perror("[CLIENT_SEND_MSG] Erro ou sinal espúrio em pthread_cond_timedwait");
                break;
            }
            // Se foi sinalizado e status mudou, o loop while terminará
        }
        
        AckStatusType current_status = ack_wait_pool[ack_wait_idx].status;
        pthread_mutex_unlock(&ack_wait_pool[ack_wait_idx].mutex);


        if (!client_keep_running) { success = -1; break; } // Verifica novamente

        if (current_status == ACK_STATUS_ACK_RECEIVED) {
            printf("[CLIENT_SEND_MSG] ACK recebido para seq=%u.\n", current_seq_num);
            success = 1;
            break; // Sucesso, sai do loop de retransmissão
        } else if (current_status == ACK_STATUS_NACK_RECEIVED) {
            printf("[CLIENT_SEND_MSG] NACK recebido para seq=%u. Falha no envio.\n", current_seq_num);
            success = -1; // Considera NACK como falha definitiva
            break;
        } else { // Timeout (wait_ret == ETIMEDOUT ou status ainda PENDING após erro/sinal)
            printf("[CLIENT_SEND_MSG] Timeout aguardando ACK/NACK para seq=%u (tentativa %d).\n", current_seq_num, attempt);
            if (attempt < current_config.max_retries) {
                last_stats.retransmissions++;
            } else {
                printf("[CLIENT_SEND_MSG] Máximo de retransmissões atingido para seq=%u.\n", current_seq_num);
                success = -1; // Falha final
            }
        }
    } // Fim loop de retransmissão

    // Limpar entrada da pool
    pthread_mutex_lock(&ack_pool_access_mutex);
    ack_wait_pool[ack_wait_idx].in_use = 0;
    ack_wait_pool[ack_wait_idx].waiting_thread_id = 0; // Limpa ID da thread
    pthread_mutex_unlock(&ack_pool_access_mutex);

    last_stats.delivery_time_ms = (clock() - send_start_time) * 1000 / CLOCKS_PER_SEC;
    
    if (success == 1) {
        printf("[CLIENT_SEND_MSG] Mensagem (seq=%u) enviada com sucesso para %s:%d.\n", current_seq_num, ip_only, port_num);
        return 0;
    } else {
        printf("[CLIENT_SEND_MSG] Falha ao enviar mensagem (seq=%u) para %s:%d.\n", current_seq_num, ip_only, port_num);
        return -1;
    }
}

void sigint_handler_client(int sig) {
    (void)sig;
    if (client_keep_running) { // Evita múltiplas impressões se SIGINT for rápido
        printf("\n[CLIENT] SIGINT recebido. Solicitando encerramento...\n");
        client_keep_running = 0; // Sinaliza para todas as threads e loops principais
    }
}

unsigned int calculate_timeout(int attempt, uint16_t base_timeout) {
    if (base_timeout == 0) base_timeout = 1; // Evitar timeout zero
    unsigned int timeout = base_timeout;
    for (int i = 0; i < attempt; ++i) {
        if ((unsigned int)-1 / 2 < timeout) { // Verifica overflow antes de multiplicar por 2
            timeout = (unsigned int)-1; // Satura no máximo se for ocorrer overflow
            break;
        }
        timeout *= 2;
    }
    return timeout;
}

//create_ack_packet_udp (já estava ok)
void create_ack_packet_udp(PowerUDPPacket* pkt, uint16_t seq_num, uint8_t type) {
    memset(pkt, 0, sizeof(PowerUDPPacket));
    pkt->header.seq_num = htons(seq_num);
    pkt->header.type = type; 
    pkt->header.payload_len = 0;
}

// receive_message (API para aplicação, já estava ok)
int receive_message(char* app_buffer, int app_bufsize) {
    pthread_mutex_lock(&queue_mutex);
    if (queue_head != queue_tail) { 
        int data_size_in_queue = message_sizes[queue_head];
        int bytes_to_copy = data_size_in_queue;
        if (data_size_in_queue > app_bufsize) {
            fprintf(stderr, "[CLIENT_RECV_MSG_API] Buffer da aplicação (%d) pequeno para dados recebidos (%d). Dados truncados.\n", app_bufsize, data_size_in_queue);
            bytes_to_copy = app_bufsize;
        }
        memcpy(app_buffer, message_queue[queue_head], bytes_to_copy);
        queue_head = (queue_head + 1) % MAX_QUEUE;
        pthread_mutex_unlock(&queue_mutex);
        return bytes_to_copy;
    }
    pthread_mutex_unlock(&queue_mutex);
    return 0; 
}

// request_protocol_config (já estava ok com a comunicação TCP melhorada)
int request_protocol_config(int enable_retransmission, int enable_backoff, 
                          int enable_sequence, uint16_t base_timeout, uint8_t max_retries) {
    if (tcp_fd < 0 || !client_keep_running) {
        fprintf(stderr, "[CLIENT_REQ_CONF] Socket TCP não conectado ou cliente encerrando.\n");
        return -1;
    }
    ClientServerTCPHeader config_req_hdr;
    config_req_hdr.message_type = TCP_MSG_TYPE_CONFIG_REQUEST;
    ConfigMessage new_config_payload = {
        .enable_retransmission = (uint8_t)enable_retransmission,
        .enable_backoff = (uint8_t)enable_backoff,
        .enable_sequence = (uint8_t)enable_sequence,
        .base_timeout = base_timeout,
        .max_retries = (uint8_t)max_retries
    };
    if (send(tcp_fd, &config_req_hdr, sizeof(config_req_hdr), 0) <= 0) {
        perror("[CLIENT_REQ_CONF] Falha ao enviar cabeçalho do pedido de config TCP"); return -1;
    }
    if (send(tcp_fd, &new_config_payload, sizeof(new_config_payload), 0) <= 0) {
        perror("[CLIENT_REQ_CONF] Falha ao enviar payload do pedido de config TCP"); return -1;
    }
    printf("[CLIENT_REQ_CONF] Pedido de nova configuração enviado ao servidor.\n");
    return 0;
}


// get_last_message_stats (já estava ok)
int get_last_message_stats(int* retransmissions_out, int* delivery_time_ms_out) {
    if (!retransmissions_out || !delivery_time_ms_out) return -1;
    *retransmissions_out = last_stats.retransmissions;
    *delivery_time_ms_out = last_stats.delivery_time_ms;
    return 0;
}

// inject_packet_loss (já estava ok)
void inject_packet_loss(int probability_percent) {
    if (probability_percent >= 0 && probability_percent <= 100) {
        packet_loss_probability = probability_percent;
        printf("[CLIENT_INFO] Probabilidade de perda de pacotes ajustada para %d%%\n", probability_percent);
    } else {
        fprintf(stderr, "[CLIENT_ERROR] Probabilidade de perda deve ser entre 0 e 100.\n");
    }
}


int main(int argc, char* argv[]) {
    srand(time(NULL)); 

    if (argc < 4) {
        fprintf(stderr, "Uso: %s <IP do servidor TCP> <porta TCP do servidor> <chave-PSK>\n", argv[0]);
        return 1;
    }
    const char* arg_server_ip = argv[1];
    int arg_server_port = atoi(argv[2]);
    const char* arg_psk = argv[3];

    if (arg_server_port <= 0 || arg_server_port > 65535) {
        fprintf(stderr, "Porta do servidor inválida: %s\n", argv[2]); return 1;
    }
    
    if (init_protocol(arg_server_ip, arg_server_port, arg_psk) < 0) {
        fprintf(stderr, "[CLIENT_MAIN] Falha na inicialização do protocolo PowerUDP.\n");
        return 1;
    }

    signal(SIGINT, sigint_handler_client);
    char input_buffer[1024];
    char command_copy[1024]; 

    printf("Cliente PowerUDP iniciado. Digite 'help' para comandos ou 'exit' para sair.\n");
    
    while (client_keep_running) {
        printf("Digite comando ou <destino> <mensagem> (ou 'exit'): ");
        fflush(stdout);

        if (fgets(input_buffer, sizeof(input_buffer), stdin) == NULL) {
            if (feof(stdin) && client_keep_running) { 
                printf("\n[CLIENT_MAIN] EOF detectado. Encerrando...\n");
            } else if (client_keep_running) { 
                // perror("[CLIENT_MAIN] Erro ao ler input"); // Pode ser devido ao cancelamento da thread
            }
            client_keep_running = 0; 
            continue; 
        }

        if (!client_keep_running) break; // Verifica se SIGINT ocorreu durante fgets

        input_buffer[strcspn(input_buffer, "\n")] = 0; 
        if (strlen(input_buffer) == 0) continue;

        strncpy(command_copy, input_buffer, sizeof(command_copy) -1);
        command_copy[sizeof(command_copy)-1] = '\0';
        char* command_token = strtok(command_copy, " ");
        if (command_token == NULL) continue;

        if (strcmp(command_token, "exit") == 0) {
            client_keep_running = 0;
        } else if (strcmp(command_token, "help") == 0) {
            // ... (impressão do help)
            printf("Comandos disponíveis:\n");
            printf("  <destino_ip:porta> <mensagem> - Envia mensagem UDP\n");
            printf("  config                        - Solicita alteração de configuração do protocolo\n");
            printf("  loss <percentual 0-100>     - Simula perda de pacotes UDP enviados/recebidos\n");
            printf("  stats                         - Mostra estatísticas da última mensagem enviada\n");
            printf("  exit                          - Encerra o cliente\n");
        } else if (strcmp(command_token, "config") == 0) {
            int req_enable_retransmission, req_enable_backoff, req_enable_sequence;
            uint16_t req_base_timeout;
            uint8_t req_max_retries_val;

            printf("Configuração do protocolo (valores atuais entre parênteses):\n");
            printf("Habilitar retransmissão (0/1) [%d]: ", current_config.enable_retransmission);
            if (scanf("%d", &req_enable_retransmission) != 1) { while(getchar()!='\n'); printf("Entrada inválida.\n"); continue; }
            while(getchar()!='\n'); 

            printf("Habilitar backoff exponencial (0/1) [%d]: ", current_config.enable_backoff);
            if (scanf("%d", &req_enable_backoff) != 1) { while(getchar()!='\n'); printf("Entrada inválida.\n"); continue; }
            while(getchar()!='\n');

            printf("Habilitar sequenciamento (0/1) [%d]: ", current_config.enable_sequence);
            if (scanf("%d", &req_enable_sequence) != 1) { while(getchar()!='\n'); printf("Entrada inválida.\n"); continue; }
            while(getchar()!='\n'); 

            printf("Timeout base (ms) [%u]: ", current_config.base_timeout);
            if (scanf("%hu", &req_base_timeout) != 1) { while(getchar()!='\n'); printf("Entrada inválida.\n"); continue; }
            while(getchar()!='\n');

            printf("Número máximo de tentativas [%u]: ", current_config.max_retries);
            if (scanf("%hhu", &req_max_retries_val) != 1) { while(getchar()!='\n'); printf("Entrada inválida.\n"); continue; }
            while(getchar()!='\n');
            
            if(request_protocol_config(req_enable_retransmission, req_enable_backoff, req_enable_sequence, req_base_timeout, req_max_retries_val) < 0){
                fprintf(stderr, "[CLIENT_MAIN_ERROR] Falha ao enviar solicitação de configuração.\n");
            }
        } else if (strcmp(command_token, "loss") == 0) {
            // ... (lógica do loss)
            char* loss_value_str = strtok(NULL, " ");
            if (loss_value_str) { int percent = atoi(loss_value_str); inject_packet_loss(percent); } 
            else { printf("Uso: loss <percentual 0-100>\n"); }
        } else if (strcmp(command_token, "stats") == 0) {
            int retrans_val; int time_val_ms;
            if (get_last_message_stats(&retrans_val, &time_val_ms) == 0) {
                printf("Estatísticas da última mensagem enviada:\n  - Retransmissões: %d\n  - Tempo de entrega: %d ms\n", retrans_val, time_val_ms);
            } else { printf("Não há estatísticas disponíveis ou erro.\n");}
        } else { 
            char* dest_str = command_token;
            char* msg_content_str = strtok(NULL, ""); 
            if (dest_str == NULL || msg_content_str == NULL || strlen(msg_content_str) == 0) {
                printf("Formato inválido. Use: <destino_ip:porta> <mensagem> ou 'help'.\n");
            } else {
                send_message(dest_str, msg_content_str, strlen(msg_content_str));
            }
        }
    }

    close_protocol_internal(0);
    printf("[CLIENT_MAIN] Cliente encerrado.\n");
    return 0;
}