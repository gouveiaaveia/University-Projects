// Francisco Gouveia 2023214517
//  João Canais 2023213000

#include "miner.h"
#include "PoW.h"
#include "statistics.h"

volatile int minning = 1;
pthread_mutex_t minning_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_t *miner_threads_global = NULL;
int number_of_miner_threads = 0;

Miner *miner_thread = NULL;

pthread_mutex_t mutex_thread = PTHREAD_MUTEX_INITIALIZER;
int block_id = 0;

enum difficulty_level random_difficulty(){
    return (enum difficulty_level)(rand() % 3);
}

void check_for_transactions() {
    int found = 1;
    int attempts = 0;
    const int max_check_attempts = 100; 
    
    while (minning && !found && attempts < max_check_attempts) {
        attempts++;
        
        for (int i = 0; i < config.POOL_SIZE; i++) {
            sem_wait(mutex);
            if (pool->slots[i].empty == 0) {
                found = 0;
                sem_post(mutex);
                break;
            } else {
                sem_post(mutex);
            }
        }
        
        usleep(100000);
    }
}

int add_transactions_to_block(Block *block, enum difficulty_level difficulty, Miner *miner_info) {
    char log_msg[256];
    char miner_id_str[32];
    snprintf(miner_id_str, sizeof(miner_id_str), "MINER %d", miner_info->id);

    int number_of_transactions_added = 0;
    int attempts = 0;
    int max_attempts = 500;

    int block_TXgen_ID_added[config.TRANSACTION_PER_BLOCK];
    memset(block_TXgen_ID_added, 0, sizeof(block_TXgen_ID_added));

    while (number_of_transactions_added < config.TRANSACTION_PER_BLOCK && minning) {
        int found_in_this_attempt = 0;

        check_for_transactions();

        if(minning == 0) {
            break;
        }
        
        for (int k = 0; k < config.POOL_SIZE; k++) {
            sem_wait(mutex);

            int i = rand() % config.POOL_SIZE + 1;

            if (pool->slots[i].empty == 0) {
                int already_added = 0;
                for (int j = 0; j < number_of_transactions_added; j++) {
                    if (block_TXgen_ID_added[j] == pool->slots[i].transaction.transaction_id) {
                        already_added = 1;
                        break;
                    }
                }

                if (!already_added) {
                    int reward = pool->slots[i].transaction.reward;
                    if ((difficulty == HIGH && reward >= 3) ||
                        (difficulty == MEDIUM && reward >= 2 && reward < 3) ||
                        (difficulty == LOW && reward < 2)) {

                        block->transactions[number_of_transactions_added] = pool->slots[i].transaction;
                        block_TXgen_ID_added[number_of_transactions_added] = pool->slots[i].transaction.transaction_id;
                        number_of_transactions_added++;
                        found_in_this_attempt = 1;

                        if (number_of_transactions_added >= config.TRANSACTION_PER_BLOCK) {
                            sem_post(mutex);
                            break;
                        }
                    }
                }
            }
            sem_post(mutex);
        }

        if (!found_in_this_attempt) {
            attempts++;
            if (attempts >= max_attempts) {
                if (difficulty == HIGH) {
                    #ifdef DEBUG
                    snprintf(log_msg, sizeof(log_msg), "No transactions found for HIGH difficulty. Lowering to MEDIUM.");
                    log_event(log_msg, miner_id_str);
                    #endif
                    difficulty = MEDIUM;
                    attempts = 0;

                } else if (difficulty == MEDIUM) {
                    #ifdef DEBUG
                    snprintf(log_msg, sizeof(log_msg), "No transactions found for MEDIUM difficulty. Lowering to LOW.");
                    log_event(log_msg, miner_id_str);
                    #endif
                    difficulty = LOW;
                    attempts = 0;

                } else if (difficulty == LOW && number_of_transactions_added == 0) {
                    #ifdef DEBUG
                    snprintf(log_msg, sizeof(log_msg), "Cannot create empty block. Waiting for any transactions...");
                    log_event(log_msg, miner_id_str);
                    #endif
                    sleep(2);
                    attempts = 0;

                } else if (difficulty == LOW && number_of_transactions_added > 0) {
                    #ifdef DEBUG
                    snprintf(log_msg, sizeof(log_msg), "Creating block with partial transactions since no more are available.");
                    log_event(log_msg, miner_id_str);
                    #endif
                    break;
                }
            }
        } else {
            attempts = 0; 
        }

        usleep(100000);
    }

    snprintf(log_msg, sizeof(log_msg), "Added %d transactions to block with difficulty %s", 
             number_of_transactions_added, 
             difficulty == HIGH ? "HIGH" : (difficulty == MEDIUM ? "MEDIUM" : "LOW"));
    log_event(log_msg, miner_id_str);
    
    block->size = number_of_transactions_added;
    block->valid = 1;

    if (number_of_transactions_added == 0) {
        snprintf(log_msg, sizeof(log_msg), "ERROR: Attempted to create empty block.");
        log_event(log_msg, miner_id_str);
        block->valid = 0;
    }

    return block->valid;
}

void create_block(Block *block, Miner *miner_info) {
    char log_msg[256];
    char miner_id_str[32];
    snprintf(miner_id_str, sizeof(miner_id_str), "MINER %d", miner_info->id);

    if(!block) {
        snprintf(log_msg, sizeof(log_msg), "Invalid block pointer.");
        log_event(log_msg, miner_id_str);
        return;
    }

    long miner_pid = pthread_self();

    snprintf(log_msg, sizeof(log_msg), "Creating Block (PID: %ld)", miner_pid);
    log_event(log_msg, miner_id_str);

    block->nonce = 0;
    block->timestamp = time(NULL);
    block->valid = 0;

    pthread_mutex_lock(&mutex_thread);
    block->id = miner_pid + block_id;
    block_id++;
    pthread_mutex_unlock(&mutex_thread);
    
    enum difficulty_level difficulty = random_difficulty();

    snprintf(log_msg, sizeof(log_msg), "Difficulty level: %s", 
             difficulty == HIGH ? "HIGH" : (difficulty == MEDIUM ? "MEDIUM" : "LOW"));
    log_event(log_msg, miner_id_str);

    int valid = add_transactions_to_block(block, difficulty, miner_info);

    if(valid){
        sem_wait(ledger_mutex); 

        if(ledger->size == 0){
            sem_post(ledger_mutex);
            memcpy(block->previous_hash, INITIAL_HASH, HASH_SIZE);
            snprintf(log_msg, sizeof(log_msg), "Using INITIAL_HASH as previous hash (first block)");
            log_event(log_msg, miner_id_str);
        } else {
            size_t ledger_block_slot_stride = sizeof(Block) + config.TRANSACTION_PER_BLOCK * sizeof(Transactions);
            Block *previous_block = (Block *)((char *)ledger->blocks + (ledger->size - 1) * ledger_block_slot_stride);
            memcpy(block->previous_hash, previous_block->hash, HASH_SIZE);
            sem_post(ledger_mutex);
            snprintf(log_msg, sizeof(log_msg), "Previous hash obtained from ledger");
            log_event(log_msg, miner_id_str);
        }
        
        PoWResult result = proof_of_work(block);

        if (result.error) {
            snprintf(log_msg, sizeof(log_msg), "Error in proof of work.");
            log_event(log_msg, miner_id_str);
            block->valid = 0;
            return;
        }

        #ifdef DEBUG
        printf("Hash: %s\n", result.hash);
        fflush(stdout);
        #endif

        strcpy(block->hash, result.hash);

        snprintf(log_msg, sizeof(log_msg), "Block created successfully. Block ID: %ld, Miner PID: %ld", 
                block->id, miner_pid);
        log_event(log_msg, miner_id_str);
    }
}

void release(int signum){
    (void)signum;
    pthread_mutex_lock(&minning_mutex);
    minning = 0;
    pthread_mutex_unlock(&minning_mutex);
}

void* mine(void *arg){
    Miner *info = (Miner *)arg;
    int id = info->id;
    char log_msg[256];
    char miner_id_str[32];
    snprintf(miner_id_str, sizeof(miner_id_str), "MINER %d", id);

    snprintf(log_msg, sizeof(log_msg), "Thread started.");
    log_event(log_msg, miner_id_str);

    int fd = -1;
    
    fd = open(PIPE_NAME, O_WRONLY);
    if (fd == -1) {
        snprintf(log_msg, sizeof(log_msg), "Error opening pipe for writing.");
        log_event(log_msg, miner_id_str);
        free(info);  // Free here if we fail to open pipe
        pthread_exit(NULL);
    }

    while(1){
        pthread_mutex_lock(&minning_mutex);
        if (minning == 0) {
            pthread_mutex_unlock(&minning_mutex);
            break;
        }
        pthread_mutex_unlock(&minning_mutex);
        
        Block *block = malloc(sizeof(Block) + config.TRANSACTION_PER_BLOCK * sizeof(Transactions));
        if (!block) {
            snprintf(log_msg, sizeof(log_msg), "Failed to allocate memory for block.");
            log_event(log_msg, miner_id_str);
            sleep(1);
            continue;
        }

        block->miner_id = id;
        block->size = config.TRANSACTION_PER_BLOCK;
        create_block(block, info);

        if (block->valid) {
            #ifdef DEBUG
            printf("Info: Miner %d created block %ld with nonce %d\n", id, block->id, block->nonce);
            fflush(stdout);
            #endif

            if (write(fd, block, sizeof(Block) + (config.TRANSACTION_PER_BLOCK * sizeof(Transactions))) == -1) {
                snprintf(log_msg, sizeof(log_msg), "Error writing block to pipe.");
                log_event(log_msg, miner_id_str);
            } else {
                snprintf(log_msg, sizeof(log_msg), "Block sent to the PIPE.");
                log_event(log_msg, miner_id_str);
            }
        } else {
            snprintf(log_msg, sizeof(log_msg), "Failed to create block: no transactions available.");
            log_event(log_msg, miner_id_str);
            sleep(1);
        }

        free(block);
        sleep(1);
    }

    if(fd != -1) {
        close(fd);
        snprintf(log_msg, sizeof(log_msg), "Pipe closed.");
        log_event(log_msg, miner_id_str);
    }

    snprintf(log_msg, sizeof(log_msg), "Thread finished.");
    log_event(log_msg, miner_id_str);
    free(info);  // Free the Miner structure only at the end of the thread
    pthread_exit(NULL);
}

void main_miner(){

    for (int i = 1; i < NSIG; i++) {
        signal(i, SIG_IGN);
    }

    srand(time(NULL) * getpid());

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = release;
    sa.sa_flags = 0;
    
    if (sigaction(SIGTERM, &sa, NULL) == -1) {
        perror("Error setting up SIGTERM handler");
        log_event("Failed to set up signal handler", "MINER");
        exit(1);
    }

    signal(SIGINT, SIG_IGN);
    
    number_of_miner_threads = config.NUM_MINERS;

    miner_threads_global = malloc(number_of_miner_threads * sizeof(pthread_t));
    if (!miner_threads_global) {
        perror("Failed to allocate memory for miner threads");
        log_event("Failed to allocate memory for miner threads", "MINER");
        exit(1);
    }

    for (int i = 0; i < number_of_miner_threads; i++) {
        Miner *miner_info = malloc(sizeof(Miner));
        if (!miner_info) {
            perror("Failed to allocate memory for thread data");
            log_event("Failed to allocate memory for thread data", "MINER");
            pthread_mutex_lock(&minning_mutex);
            minning = 0;
            pthread_mutex_unlock(&minning_mutex);
            free(miner_threads_global);
            exit(1);
        }

        miner_info->id = i; 

        if (pthread_create(&miner_threads_global[i], NULL, mine, miner_info) != 0) {
            perror("Error creating miner thread");
            log_event("Error creating miner thread", "MINER");
            free(miner_info);
            pthread_mutex_lock(&minning_mutex);
            minning = 0;
            pthread_mutex_unlock(&minning_mutex);
            free(miner_threads_global);
            exit(1);
        }
    }

    // Wait for threads to finish
    for (int i = 0; i < number_of_miner_threads; i++) {
        pthread_join(miner_threads_global[i], NULL);
        log_event("Miner thread joined successfully.", "MINER");
    }

    free(miner_threads_global);
    miner_threads_global = NULL;
    pthread_mutex_destroy(&mutex_thread);
    pthread_mutex_destroy(&minning_mutex);
}
