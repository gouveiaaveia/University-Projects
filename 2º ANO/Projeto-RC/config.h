#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>
#include <sys/types.h>

// Tipos de mensagem PowerUDP (para UDP e Multicast)
#define MSG_TYPE_DATA 0
#define MSG_TYPE_ACK 1
#define MSG_TYPE_NACK 2
#define MSG_TYPE_DISCONNECT_UDP 3
#define MSG_TYPE_SERVER_SHUTDOWN 4

// Estrutura de configuração do PowerUDP
typedef struct {
    uint8_t enable_retransmission;
    uint8_t enable_backoff;
    uint8_t enable_sequence;
    uint16_t base_timeout;
    uint8_t max_retries;
} ConfigMessage;

// Estrutura do cabeçalho PowerUDP
typedef struct {
    uint16_t seq_num;      // Número de sequência
    uint8_t type;          // MSG_TYPE_DATA, MSG_TYPE_ACK, etc.
    uint16_t payload_len;  // Tamanho do payload 
} PowerUDPHeader;

// Estrutura completa do pacote PowerUDP
typedef struct {
    PowerUDPHeader header;
    char payload[1024];
} PowerUDPPacket;

// Mensagem de registro (TCP)
typedef struct {
    char psk[64];      
} RegisterMessage;

// ---- Novas definições para comunicação TCP Cliente-Servidor ----
#define TCP_MSG_TYPE_CONFIG_REQUEST 1
#define TCP_MSG_TYPE_DISCONNECT_REQUEST 2

// Cabeçalho para mensagens TCP entre cliente e servidor (após registo)
typedef struct {
    uint8_t message_type; // TCP_MSG_TYPE_CONFIG_REQUEST ou TCP_MSG_TYPE_DISCONNECT_REQUEST
} ClientServerTCPHeader;

// Endereços multicast
#define MULTICAST_GROUP "239.0.0.1"
#define MULTICAST_PORT 5000
#define MAX_QUEUE 100

#endif