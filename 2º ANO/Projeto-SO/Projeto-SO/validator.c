// Francisco Gouveia 2023214517
//  João Canais 2023213000

#include "controller.h"
#include "miner.h"
#include "PoW.h"
#include "statistics.h"

int total_valid_blocks;
int total_invalid_blocks;
int blocks_in_blockchain;
int current_validators = 1; 
int validating = 1;

volatile sig_atomic_t should_terminate = 0;

extern int controller_pid;

typedef struct {
    int id;
    pid_t pid;
} Validator;

Validator validators_pdid[3];

int found_id_validator (pid_t pid){
    for (int i = 0; i < 3; i++){
        if (validators_pdid[i].pid == pid){
            return validators_pdid[i].id;
        }
    }

    return 1;
}

void handle_termination(int signum) {
    (void)signum;
    should_terminate = 1;
}

void verify_Pool() {
    sem_wait(mutex);
    int occupied_slots = 0;
    for (int i = 0; i < pool->pool_size; i++) {
        if (pool->slots[i].empty == 0) {
            occupied_slots++;
        }
    }
    sem_post(mutex);

    float occupancy_percentage = ((float)occupied_slots / pool->pool_size) * 100;

    sem_wait(validator_mutex);
    
    if (occupancy_percentage < 40.0) {
        for (int i = 2; i >= 1; i--) {  
            if (validators_pdid[i].pid != 0) {  
                int validator_id = validators_pdid[i].id;
                pid_t pid_to_terminate = validators_pdid[i].pid;

                // Envia SIGTERM para o validator terminar graciosamente
                kill(pid_to_terminate, SIGTERM);
                
                // Espera o processo terminar
                int status;
                waitpid(pid_to_terminate, &status, 0);

                // Depois de confirmar que o processo terminou, registra no log
                char log_message[128];
                snprintf(log_message, sizeof(log_message), "VALIDATOR %d TERMINATED", validator_id);
                log_event(log_message, "VALIDATOR");

                // Limpa a entrada no array
                validators_pdid[i].id = 0;
                validators_pdid[i].pid = 0;
                current_validators--;
            }
       }
    } else if (occupancy_percentage > 60.0 && occupancy_percentage <= 80.0) {
        printf("Occupancy percentage: %.2f%%\n", occupancy_percentage);
        fflush(stdout);
        while (current_validators < 2) {
            pid_t pid = fork();
            if (pid == 0) {
                log_event("READY FOR WORK", "VALIDATOR");
                validators_pdid[current_validators].pid = getpid();
                validators_pdid[current_validators].id = current_validators + 1;
                main_validator();
                exit(0);

            } else if (pid > 0) {
                // Update the array in the parent process
                validators_pdid[current_validators].pid = pid;
                validators_pdid[current_validators].id = current_validators + 1;

                char log_message[128];
                snprintf(log_message, sizeof(log_message), "VALIDATOR %d CREATED", current_validators + 1);
                log_event(log_message, "VALIDATOR");

                current_validators++;
            } else {
                perror("Error creating validator process.");
            }
        }
    } else if (occupancy_percentage > 80.0) {
        while (current_validators < 3) {
            pid_t pid = fork();
            if (pid == 0) {
                log_event("READY FOR WORK", "VALIDATOR");
                validators_pdid[current_validators].pid = getpid();
                validators_pdid[current_validators].id = current_validators + 1;
                main_validator();
                exit(0);

            } else if (pid > 0) {
                // Update the array in the parent process
                validators_pdid[current_validators].pid = pid;
                validators_pdid[current_validators].id = current_validators + 1;

                char log_message[128];
                snprintf(log_message, sizeof(log_message), "VALIDATOR %d CREATED", current_validators + 1);
                log_event(log_message, "VALIDATOR");

                current_validators++;
            } else {
                perror("Error creating validator process.");
            }
        }
    }
    #ifdef DEBUG
    printf("Current validators: %d\n", current_validators);
    fflush(stdout);
    #endif
    sem_post(validator_mutex);
}

int recheck_PoW (Block *block){
    return verify_nonce(block);
}

//checks that it correctly references the latest accepted block in the Blockchain
//Ledger, typically by matching the Previous_Block_Hash
int check_Hash (Block *block){
    sem_wait(ledger_mutex);
    
    if (ledger->size == 0) {
        sem_post(ledger_mutex);
        return 1;
    }

    size_t ledger_block_slot_stride = sizeof(Block) + config.TRANSACTION_PER_BLOCK * sizeof(Transactions);
    Block *last_block = (Block *)((char *)ledger->blocks + (ledger->size - 1) * ledger_block_slot_stride);

    if (strncmp(block->previous_hash, last_block->hash, HASH_SIZE) == 0) {
        sem_post(ledger_mutex);
        return 1;
    } else {
        sem_post(ledger_mutex);
        return 0;
    }
}

//FEITA
int transactions_in_Pool (Block *block){

    sem_wait(mutex);
    int count_transactions_block = block->size;
    int count = 0;

    for (int i = 0; i < config.TRANSACTION_PER_BLOCK; i++){
        for (int j = 0; j < config.POOL_SIZE; j++){

            if (block->transactions[i].transaction_id == pool->slots[j].transaction.transaction_id && pool->slots[j].empty == 0){
                count ++;
                break;
            }
        }
    }

    if (count == count_transactions_block){
        sem_post(mutex);
        return 1;
    }

    sem_post(mutex);
    return 0;
}

int put_block_in_ledger(Block *block){

    char log_message[128];
    char validator_id_str[32];
    int validator_id = found_id_validator(getpid());
    snprintf(validator_id_str, sizeof(validator_id_str), "VALIDATOR %d", validator_id);

    if (check_Hash(block) == 0){
        fprintf(stderr, "Error: Block does not reference the latest accepted block.\n");
        return 0;
    }

    sem_wait(ledger_mutex); 

    if (ledger->size < config.BLOCKCHAIN_BLOCKS) {
        size_t ledger_block_slot_stride = sizeof(Block) + config.TRANSACTION_PER_BLOCK * sizeof(Transactions);
        Block *dest_block_in_ledger = (Block *)((char *)ledger->blocks + ledger->size * ledger_block_slot_stride);
        memcpy(dest_block_in_ledger, block, sizeof(Block) + block->size * sizeof(Transactions));

        snprintf(log_message, sizeof(log_message), "Block %ld added to the ledger", block->id);
        log_event(log_message, validator_id_str);

        ledger->size++;

    } else {
        snprintf(log_message, sizeof(log_message), "Ledger is full. Cannot insert block %ld.", block->id);
        log_event(log_message, validator_id_str);
        sem_post(ledger_mutex);
        
        kill(controller_pid, SIGINT);
        
        return 0; 
    }

    sem_post(ledger_mutex);
    return 1;
}

void send_block_to_statistics(Block *block, int verification) {
    int validator_id = found_id_validator(getpid());
    char log_message[128];
    char validator_id_str[32];
    snprintf(validator_id_str, sizeof(validator_id_str), "VALIDATOR %d", validator_id);
    
    size_t fixed_payload_size = sizeof(BlockStatsFixedPayload);
    size_t transactions_data_size = block->size * sizeof(Transactions);
    size_t total_data_payload_size = fixed_payload_size + transactions_data_size;

    size_t total_msg_buffer_size = sizeof(long) + total_data_payload_size;
    void *msg_buffer = malloc(total_msg_buffer_size);

    if (!msg_buffer) {
        snprintf(log_message, sizeof(log_message), "Failed to allocate memory for statistics message");
        log_event(log_message, validator_id_str);
        return;
    }

    *(long*)msg_buffer = 1;

    char *data_ptr = (char*)msg_buffer + sizeof(long);

    BlockStatsFixedPayload *fixed_payload_ptr = (BlockStatsFixedPayload *)data_ptr;
    fixed_payload_ptr->validity_status = verification;
    fixed_payload_ptr->miner_id = block->miner_id;
    fixed_payload_ptr->block_size = block->size;

    if (block->size > 0) {
        memcpy(data_ptr + fixed_payload_size, block->transactions, transactions_data_size);
    }

    // The 3rd argument to msgsnd is the size of the data payload (mtext)
    if (msgsnd(mqid_msg, msg_buffer, total_data_payload_size, 0) == -1) {
        snprintf(log_message, sizeof(log_message), "Error sending message to statistics: %s", strerror(errno));
        log_event(log_message, validator_id_str);
    }

    free(msg_buffer); // Free the dynamically allocated buffer
}

// FEITA
void put_the_age() {
    sem_wait(mutex);

    int j = 0;

    while(j < pool->transactions_in_pool) {
        if (pool->slots[j].empty == 0) {

            pool->slots[j].age++;

            if (pool->slots[j].age % 50 == 0){
                pool->slots[j].transaction.reward++;
            }
        }
        j++;
    }

    sem_post(mutex);
}


void clean_transactions(Block *block){
    int validator_id = found_id_validator(getpid());
    char log_message[128];
    char validator_id_str[32];
    snprintf(validator_id_str, sizeof(validator_id_str), "VALIDATOR %d", validator_id);

    put_the_age();
    
    // Apagar da Pool todas as transactions que estão no bloco
    sem_wait(mutex);
    snprintf(log_message, sizeof(log_message), "CLEANING TRANSACTIONS");
    log_event(log_message, validator_id_str);
    for (int i = 0; i < config.TRANSACTION_PER_BLOCK; i++){
        for (int j = 0; j < config.POOL_SIZE; j++){
            if (block->transactions[i].transaction_id == pool->slots[j].transaction.transaction_id){
                pool->slots[j].empty = 1;
                pool->slots[j].age = 0;

                pool->slots[j].transaction.transaction_id = 0;
                pool->slots[j].transaction.receiver_ID = 0; 
                pool->slots[j].transaction.sender_ID = 0;
                pool->slots[j].transaction.value = 0;
                pool->slots[j].transaction.reward = 0;
                pool->slots[j].transaction.timestamp = 0;
                pool->transactions_in_pool--;

                sem_post(empty); // Adiciona um slot vazio à pool
            }
        }
    }
    sem_post(mutex);
}

void invalidate_block(Block *block){
    // Implementar a invalidação do bloco aqui
    block->valid = 0;
    total_invalid_blocks++;
    char log_message[128];
    char validator_id_str[32];
    int validator_id = found_id_validator(getpid());
    snprintf(validator_id_str, sizeof(validator_id_str), "VALIDATOR %d", validator_id);
    snprintf(log_message, sizeof(log_message), "BLOCK FROM MINER %d INVALID", block->miner_id);
    log_event(log_message, validator_id_str);
    send_block_to_statistics(block, 0);
}

void validate_block(Block *block, int validator_id){
    put_the_age();
    
    int pow_valid = recheck_PoW(block);
    int hash_valid = check_Hash(block);
    int tx_valid = transactions_in_Pool(block);
    
    #ifdef DEBUG
    printf("Verification results: PoW=%d, Hash=%d, Txs=%d\n", pow_valid, hash_valid, tx_valid);
    fflush(stdout);
    #endif
    
    if (pow_valid && hash_valid && tx_valid) {

        if (put_block_in_ledger(block) == 0){
            invalidate_block(block);
            return;
        }

        block->valid = 1;
        total_valid_blocks++;
        char log_message[128];
        char validator_id_str[32];
        snprintf(validator_id_str, sizeof(validator_id_str), "VALIDATOR %d", validator_id);
        snprintf(log_message, sizeof(log_message), "BLOCK FROM MINER %d VALID", block->miner_id);
        log_event(log_message, validator_id_str);

        clean_transactions(block);
        send_block_to_statistics(block, 1);

        snprintf(log_message, sizeof(log_message), "BLOCK FROM MINER %d INSERTED IN BLOCKCHAIN!", block->miner_id);
        log_event(log_message, validator_id_str);
        blocks_in_blockchain++;     
    } else {
        #ifdef DEBUG
        printf("Block validation failed: PoW=%d, Hash=%d, Txs=%d\n", pow_valid, hash_valid, tx_valid);
        #endif
        invalidate_block(block);
    }
}

void main_validator(){

    for (int i = 1; i < NSIG; i++) {
        signal(i, SIG_IGN);
    }

    int validator_id = found_id_validator(getpid());
    char log_message[128];
    char validator_id_str[32];
    snprintf(validator_id_str, sizeof(validator_id_str), "VALIDATOR %d", validator_id);
    snprintf(log_message, sizeof(log_message), "Starting...");
    log_event(log_message, validator_id_str);

    // Signal handler for SIGTERM
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handle_termination;

    if (sigaction(SIGTERM, &sa, NULL) == -1) {
        perror("Error setting up SIGTERM handler");
        log_event("Failed to set up signal handler", validator_id_str);
        exit(1);
    }

    key_msg = ftok(".", 67); 
    if (key_msg == (key_t)-1) {
        perror("Error generating key for message queue");
        log_event("Failed to generate message queue key", validator_id_str);
        exit(1);
    }

    mqid_msg = msgget(key_msg, 0777);
    if (mqid_msg == -1) {
        perror("msgget");
        log_event("Failed to get message queue", validator_id_str);
        exit(1);
    }
    
    int fd = open(PIPE_NAME, O_RDONLY);
    if (fd == -1) {
        perror("Error opening pipe for reading.");
        snprintf(log_message, sizeof(log_message), "Failed to open pipe");
        log_event(log_message, validator_id_str);
        exit(1);
    }
    
    snprintf(log_message, sizeof(log_message), "Pipe opened successfully");
    log_event(log_message, validator_id_str);
    
    char *buffer = malloc(sizeof(Block) + (config.TRANSACTION_PER_BLOCK * sizeof(Transactions)));
    if (!buffer) {
        perror("Failed to allocate memory for block buffer");
        log_event("Failed to allocate memory for block buffer", validator_id_str);
        close(fd);
        exit(1);
    }

    while(validating && !should_terminate){
        snprintf(log_message, sizeof(log_message), "Waiting for block from pipe...");
        log_event(log_message, validator_id_str);
        
        ssize_t bytes_read = read(fd, buffer, sizeof(Block) + (config.TRANSACTION_PER_BLOCK * sizeof(Transactions)));
        if(bytes_read == -1){
            perror("Error reading from pipe.");
            snprintf(log_message, sizeof(log_message), "Failed to read from pipe");
            log_event(log_message, validator_id_str);
            free(buffer);
            close(fd);
            exit(1);
        } else if (bytes_read == 0) {
            snprintf(log_message, sizeof(log_message), "Pipe closed");
            log_event(log_message, validator_id_str);
            break;
        }
        
        snprintf(log_message, sizeof(log_message), "Block received from pipe");
        log_event(log_message, validator_id_str);
        
        Block *block = (Block *)buffer;

        snprintf(log_message, sizeof(log_message), "STARTED VALIDATING BLOCK FROM MINER %d", block->miner_id);
        log_event(log_message, validator_id_str);

        if (block != NULL) {
            validate_block(block, validator_id);
        }
        verify_Pool();
    }
    
    free(buffer);
    close(fd);
    snprintf(log_message, sizeof(log_message), "Exiting");
    log_event(log_message, validator_id_str);
}
