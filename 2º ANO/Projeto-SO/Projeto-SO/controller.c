// Francisco Gouveia 2023214517
//  João Canais 2023213000

#include "controller.h"
#include "miner.h"
#include "statistics.h"

#define DEBUG

Config config;

int controller_pid;

//transaction pool
int shmid_transaction_pool;
key_t shmkey_transaction_pool;
sem_t *mutex; // transaction pool semaphore
sem_t *empty; // transaction pool semaphore
Transaction_Pool *pool;

// blockchain
int shmid_blockchain_ledger;
key_t shmkey_blockchain_ledger;
sem_t *ledger_mutex; // blockchain ledger semaphore
Blockchain_Ledger *ledger;	

// miner statistics
int shmid_miner_statistics;
key_t shmkey_miner_statistics;
sem_t *miner_mutex; // miner statistics semaphore for the case of multiple validators

// Validator semaphore
sem_t *validator_mutex;

//Statistics
Statistics statistics;

// Message Queue
int mqid;
key_t mq_key;

sem_t *log_mutex;

int miner_pid;
int validator_pid;
int statistics_pid;

FILE *log_file;

void read_conf_file(Config *config){
    FILE *file = fopen("config.cfg", "r");
    char line[64];
    int i = 0;

    if(file == NULL){
        printf("Error: %s\n", strerror(errno));
        return;
    }

    while(fgets(line, sizeof(line), file)){
        i++;
        if(i == 1){
            config->NUM_MINERS = atoi(line);
        }else if(i == 2){
            config->POOL_SIZE = atoi(line);
        }else if(i == 3){
            config->TRANSACTION_PER_BLOCK = atoi(line);
        }else if(i == 4){
            config->BLOCKCHAIN_BLOCKS = atoi(line);
        }
    }

    if(config->NUM_MINERS <= 0 || config->POOL_SIZE <= 0 || config->TRANSACTION_PER_BLOCK <= 0 || config->BLOCKCHAIN_BLOCKS <= 0) {
        log_event("Error: Invalid configuration values in config.cfg. All values must be positive integers.", "CONTROLLER");
        fclose(file);
        exit(1);
    }
    
    fclose(file);
}

void log_event(const char *event, const char *process) {
    sem_wait(log_mutex);

    if (process) {
        time_t now = time(NULL);
        char timestamp[9]; // Formato HH:MM:SS, incluindo o terminador nulo
        strftime(timestamp, 9, "%H:%M:%S", localtime(&now));

        fprintf(log_file, "%s %s: %s\n", timestamp, process, event);
        printf("%s %s: %s\n", timestamp, process, event);
    } else {
        fprintf(log_file, "%s\n", event);
        printf("%s\n", event);
    }

    fflush(log_file);
    sem_post(log_mutex);
}

void initialize_resources(){
    log_event("DEI_CHAIN SIMULATOR STARTING", "CONTROLLER");

    shmkey_transaction_pool = ftok(".", 65);
    if (shmkey_transaction_pool == (key_t)-1) {
        perror("IPC error: ftok");
        exit(1);
    }

    // Calculate total required size including transactions embedded in slots
    size_t shared_mem_size = sizeof(Transaction_Pool) + (config.POOL_SIZE * sizeof(Slot));

    // Create shared memory with adjusted size
    shmid_transaction_pool = shmget(shmkey_transaction_pool, shared_mem_size, IPC_CREAT | IPC_EXCL | 0777);
    if (shmid_transaction_pool < 1) {
        log_event("Error creating shared memory!\n", "CONTROLLER");
        exit(1);
    }

    log_event("SHM_TX_POOL CREATED", "CONTROLLER");

    // Attach shared memory
    pool = (Transaction_Pool *)shmat(shmid_transaction_pool, NULL, 0);
    if (pool == (Transaction_Pool *)-1) {
        log_event("Error attaching shared memory!\n", "CONTROLLER");
        exit(1);
    }

    pool->pool_size = config.POOL_SIZE;
    
    // Initialize slots with empty flag
    for(int i = 0; i < config.POOL_SIZE; i++){
        pool->slots[i].empty = 1;
        pool->slots[i].age = 0;
    }

    shmkey_blockchain_ledger = ftok(".", 66);
    if (shmkey_blockchain_ledger == (key_t)-1) {
        perror("IPC error: ftok");
        exit(1);
    }

    size_t shared_mem_size_ledger = sizeof(Blockchain_Ledger) + 
                                    (config.BLOCKCHAIN_BLOCKS * 
                                     (sizeof(Block) + config.TRANSACTION_PER_BLOCK * sizeof(Transactions)));

    shmid_blockchain_ledger = shmget(shmkey_blockchain_ledger, shared_mem_size_ledger, IPC_CREAT | IPC_EXCL | 0777);
    if (shmid_blockchain_ledger < 1) {
        perror("Error creating shared memory!\n");
        exit(1);
    }

    log_event("SHM_LEDGER CREATED", "CONTROLLER");

    ledger = (Blockchain_Ledger *)shmat(shmid_blockchain_ledger, NULL, 0);
    if (ledger == (Blockchain_Ledger *)-1) {
        perror("Error attaching shared memory!\n");
        exit(1);
    }

    ledger->size = 0;

    // Initialize miner statistics shared memory
    shmid_miner_statistics = shmget(shmkey_miner_statistics, sizeof(Miner), IPC_CREAT | IPC_EXCL | 0777);
    if (shmid_miner_statistics < 1) {
        perror("Error creating shared memory!\n");
        exit(1);
    }

    //Inicializar a pipe
    unlink(PIPE_NAME);
    if ((mkfifo(PIPE_NAME, 0777)<0) && (errno!= EEXIST)) {
        log_event("Failure creating named pipe", "CONTROLLER");
        exit(1);
    }
    log_event("NAMED PIPE CREATED", "CONTROLLER");
    

    //Inicializar a MessageQueue
    mq_key = ftok(".", 67); // Gerar uma chave única para a message queue
    if (mq_key == (key_t)-1) {
        perror("Error generating key for message queue");
        exit(1);
    }

    mqid = msgget(mq_key, IPC_CREAT | 0777);
    if (mqid == -1) {
        perror("msgget");
        exit(1);
    }

    log_event("MESSAGE QUEUE CREATED", "CONTROLLER");

    // Inicializar os semáforos

    sem_unlink("Validator_MUTEX");
    validator_mutex = sem_open("Validator_MUTEX", O_CREAT | O_EXCL, 0777, 1);
    if (validator_mutex == SEM_FAILED) {
        log_event("Failure creating the semaphore Validator_MUTEX", "CONTROLLER");
        exit(1);
    }

    // Semáforo para Transaction Pool
    sem_unlink("EMPTY");
    empty = sem_open("EMPTY", O_CREAT | O_EXCL, 0777, config.POOL_SIZE);
    if (empty == SEM_FAILED) {
        log_event("Failure creating the semaphore EMPTY", "CONTROLLER");
        exit(1);
    }

    // Semáforo para a Transaction Pool mutex
    sem_unlink("MUTEX");
    mutex = sem_open("MUTEX", O_CREAT | O_EXCL, 0777, 1);
    if (mutex == SEM_FAILED) {
        log_event("Failure creating the semaphore MUTEX", "CONTROLLER");
        exit(1);
    }

    
    // Semáforo para Blockchain Ledger mutex
    sem_unlink("LEDGER_MUTEX");
    ledger_mutex = sem_open("LEDGER_MUTEX", O_CREAT | O_EXCL, 0777, 1);
    if (ledger_mutex == SEM_FAILED) {
        log_event("Failure creating the semaphore LEDGER_MUTEX", "CONTROLLER");
        exit(1);
    }

    printf("Resources initialized succefuly!\n");
}

void initialize_processes(){
    validator_pid = fork();

    if(validator_pid == -1){
        char error_message[256];
        snprintf(error_message, sizeof(error_message), "Error creating validator process: %s", strerror(errno));
        log_event(error_message, "CONTROLLER");
        release_resources();
        exit(0);
    }

    if(validator_pid == 0){
        log_event("PROCESS VALIDATOR CREATED", "CONTROLLER");
        main_validator();
        exit(0);
    }

    miner_pid = fork();

    if(miner_pid == -1){
        char error_message[256];
        snprintf(error_message, sizeof(error_message), "Error creating miner process: %s", strerror(errno));
        log_event(error_message, "CONTROLLER");
        release_resources();
        exit(0);
    }

    if(miner_pid == 0){
        log_event("PROCESS MINER CREATED", "CONTROLLER");
        main_miner();
        exit(0);
    }

    statistics_pid = fork();

    if(statistics_pid == -1){
        char error_message[256];
        snprintf(error_message, sizeof(error_message), "Error creating statitics process: %s", strerror(errno));
        log_event(error_message, "CONTROLLER");
        release_resources();
        exit(0);
    }

    if(statistics_pid == 0){
        log_event("PROCESS STATISTICS CREATED", "CONTROLLER");
        main_statistics();
        exit(0);
    }

    
    printf("Processes initialized succefuly!\n");
}

void release_resources(){
    if (getpid() != controller_pid) return;

    // Adicionar verificação para evitar dupla liberação
    static volatile int resources_released = 0;
    if (resources_released) return;
    resources_released = 1;

    log_event("Releasing resources and closing program.", "CONTROLLER");
    
    // Enviar sinal para processos filhos terminarem
    if (miner_pid > 0) kill(miner_pid, SIGTERM);
    if (validator_pid > 0) kill(validator_pid, SIGTERM);
    if (statistics_pid > 0) kill(statistics_pid, SIGTERM);
    
    usleep(10000);
    // Esperar que os processos terminem antes de remover recursos compartilhados
    if (validator_pid > 0) waitpid(validator_pid, NULL, 0);
    log_event("Validator process terminated", "CONTROLLER");
    if (statistics_pid > 0) waitpid(statistics_pid, NULL, 0);
    log_event("Statistics process terminated", "CONTROLLER");
    if (miner_pid > 0) waitpid(miner_pid, NULL, 0);
    log_event("Miner process terminated", "CONTROLLER");

    log_event("Dumping the Ledger", "CONTROLLER");
    write_ledger(ledger);

    // Fechar e remover semáforos
    if (validator_mutex != SEM_FAILED && validator_mutex != NULL) {
        sem_close(validator_mutex);
        sem_unlink("Validator_MUTEX");
    }

    if (mutex != SEM_FAILED && mutex != NULL) {
        sem_close(mutex);
        sem_unlink("MUTEX");
    }
    
    if (empty != SEM_FAILED && empty != NULL) {
        sem_close(empty);
        sem_unlink("EMPTY");
    }

    if (ledger_mutex != SEM_FAILED && ledger_mutex != NULL) {
        sem_close(ledger_mutex);
        sem_unlink("LEDGER_MUTEX");
    }
    
    if (pool != NULL && pool != (Transaction_Pool *)-1) {
        shmdt(pool);
        if (shmid_transaction_pool > 0) {
            shmctl(shmid_transaction_pool, IPC_RMID, NULL);
        }
    }
    
    if (ledger != NULL && ledger != (Blockchain_Ledger *)-1) {
        shmdt(ledger);
        if (shmid_blockchain_ledger > 0) {
            shmctl(shmid_blockchain_ledger, IPC_RMID, NULL);
        }
    }
    
    if (mqid > 0) {
        msgctl(mqid, IPC_RMID, NULL);
    }
    
    unlink(PIPE_NAME);
    
    if (log_file != NULL) {
        fclose(log_file);
    }
    
    if (log_mutex != SEM_FAILED && log_mutex != NULL) {
        sem_close(log_mutex);
        sem_unlink("LOG_MUTEX");
    }

    printf("Resources released successfully!\n");

    exit(0);
}

void cleanup_existing_resources() {
    sem_unlink("MUTEX");
    sem_unlink("EMPTY");
    sem_unlink("LOG_MUTEX");
    sem_unlink("LEDGER_MUTEX");
    
    unlink(PIPE_NAME);
    
    // Try to remove shared memory if it exists
    key_t key1 = ftok(".", 65);
    key_t key2 = ftok(".", 66);
    
    int shmid1 = shmget(key1, 0, 0);
    if (shmid1 >= 0) {
        shmctl(shmid1, IPC_RMID, NULL);
    }
    
    int shmid2 = shmget(key2, 0, 0);
    if (shmid2 >= 0) {
        shmctl(shmid2, IPC_RMID, NULL);
    }
}

// Função para escrever o Ledger no arquivo de log
void write_ledger(Blockchain_Ledger *ledger) {
    sem_wait(ledger_mutex);
    log_event("\n=================== Start Ledger ===================",NULL);

    size_t ledger_block_slot_stride = sizeof(Block) + config.TRANSACTION_PER_BLOCK * sizeof(Transactions);

    for (int i = 0; i < ledger->size; i++) {

        Block *block = (Block *)((char *)ledger->blocks + i * ledger_block_slot_stride);
        char log_message[512];

        snprintf(log_message, sizeof(log_message), "||---- Block %03d --", i);
        log_event(log_message,NULL);
        snprintf(log_message, sizeof(log_message), "Block ID: BLOCK-%ld-%d", block->id, i);
        log_event(log_message,NULL);
        snprintf(log_message, sizeof(log_message), "Hash:%s", block->hash);
        log_event(log_message,NULL);
        snprintf(log_message, sizeof(log_message), "Previous Hash:%s", block->previous_hash);
        log_event(log_message,NULL);
        snprintf(log_message, sizeof(log_message), "Block Timestamp: %ld", block->timestamp);
        log_event(log_message,NULL);
        snprintf(log_message, sizeof(log_message), "Nonce: %d", block->nonce);
        log_event(log_message,NULL);

        log_event("Transactions:",NULL);
        for (int j = 0; j < block->size; j++) {
            Transactions *transaction = &block->transactions[j];
            snprintf(log_message, sizeof(log_message),
                     "    [%d] ID: TX-%d-%d | Reward: %d | Value: %.2d | Timestamp: %ld",
                     j, transaction->transaction_id, j, transaction->reward, transaction->value, transaction->timestamp);
            log_event(log_message,NULL);
        }
        log_event("||------------------------------",NULL);
    }
    log_event("=================== End Ledger ===================\n",NULL);
    sem_post(ledger_mutex);
}

void handle_signals(int signum) {
    if (signum == SIGUSR1) {
        log_event("Received SIGUSR1 signal", "CONTROLLER");
        kill(statistics_pid, SIGUSR1);
    } else if (signum == SIGINT) {
        if (getpid() != controller_pid) return;
        kill(statistics_pid, SIGUSR1);
        log_event("Received SIGINT signal", "CONTROLLER");
        release_resources();
    }
}

int main(){

    controller_pid = getpid();

    printf("%d\n\n\n",controller_pid);

    for (int i = 1; i < NSIG; i++) {
        signal(i, SIG_IGN);
    }

    cleanup_existing_resources();
    
    log_file = fopen("DEIChain_log.txt", "w");
    if (log_file == NULL) {
        perror("Error opening log file");
        exit(1);
    }

    sem_unlink("LOG_MUTEX");
    log_mutex = sem_open("LOG_MUTEX", O_CREAT | O_EXCL, 0777, 1);
    if (log_mutex == SEM_FAILED) {
        fprintf(log_file, "Failure creating the semaphore LOG_MUTEX\n");
        fclose(log_file);
        exit(1);
    }
    
    pool = NULL;
    ledger = NULL;
    mutex = NULL;
    empty = NULL;

    read_conf_file(&config);
    initialize_resources();
    initialize_processes();

    signal(SIGINT, handle_signals);
    signal(SIGUSR1, handle_signals);
    
    while(1){
        pause();
    }
    
    return 0;
}
