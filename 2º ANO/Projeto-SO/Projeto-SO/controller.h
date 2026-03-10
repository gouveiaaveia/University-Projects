// Francisco Gouveia 2023214517
//  João Canais 2023213000

#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <errno.h>
#include <string.h>
#include <pthread.h>
#include <semaphore.h>
#include <signal.h>
#include <time.h>
#include <fcntl.h>
#include <stdbool.h>
#include <sys/msg.h>
#include <sys/stat.h>
#include <openssl/sha.h>
#include <math.h>


#define PIPE_NAME "/tmp/VALIDATOR_INPUT"

#define HASH_SIZE 65
#define TXB_ID_LEN 64

typedef struct{
    int NUM_MINERS;
    int POOL_SIZE;
    int TRANSACTION_PER_BLOCK;
    int BLOCKCHAIN_BLOCKS;
}Config;

extern Config config;

typedef struct {
    int transaction_id;
    int receiver_ID;
    int sender_ID;
    int value;
    int reward;
    time_t timestamp;
} Transactions;

typedef struct{
    int age;
    int empty; // 1 - occupied, 0 - empty
    Transactions transaction;
}Slot;

typedef struct {
    int pool_size;
    int transactions_in_pool;
    Slot slots[];
}Transaction_Pool;

typedef struct{
    long id;
    int miner_id;
    int size;
    int valid;
    unsigned int nonce;
    char previous_hash[HASH_SIZE];
    char hash[HASH_SIZE];
    time_t timestamp;
    Transactions transactions[];
}Block;

typedef struct{
    int size;
    Block blocks[];
}Blockchain_Ledger;


extern Transaction_Pool *pool;
extern Blockchain_Ledger *ledger;
extern sem_t *mutex;
extern sem_t *empty;
extern sem_t *ledger_mutex;
extern sem_t *ledger_empty;
extern sem_t *log_mutex;
extern sem_t *validator_mutex;

extern key_t key_msg;
extern int mqid_msg;

void initialize_resources();
void initialize_processes();

void read_conf_file(Config *config);
void release_resources();
void log_event(const char *event, const char *process);
void write_ledger(Blockchain_Ledger *ledger);

void main_miner();
void main_validator();

#endif
