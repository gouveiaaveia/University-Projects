// Francisco Gouveia 2023214517
//  João Canais 2023213000

#include "controller.h"

#define DEBUG 1

int reward;
int sleep_time;
int incrementer = 0;

int shmid_transaction;
sem_t *mutex;
sem_t *empty;
key_t shmkey_transaction_pool;
Transaction_Pool *pool;

void transaction_maker(int reward) {
    int pid = getpid();
    int found = 0;

    int pool_size = pool->pool_size;

    Transactions transaction;
    transaction.transaction_id = pid + incrementer + 1;
    transaction.value = (float)(rand() % 1000) / 10.0;
    transaction.reward = reward;
    transaction.sender_ID = pid;
    transaction.receiver_ID = rand() % 100;
    transaction.timestamp = time(NULL);


    sem_wait(empty);
    sem_wait(mutex);

    incrementer++;

    for(int i = 0; i < pool_size; i++) {
        if(pool->slots[i].empty) {
            
            pool->slots[i].transaction = transaction;
            pool->slots[i].age = 0;
            pool->slots[i].empty = 0;
            pool->transactions_in_pool++;

            #ifdef DEBUG
            printf("Added transaction %d (PID: %d)\n", i, pid);
            printf("Transaction ID: %d\n", pool->slots[i].transaction.transaction_id);
            #endif
            
            found = 1;
            break;
        }
    }

    if(found == 0) {
        printf("Pool is full, waitting for space!\n");
    }

    sem_post(mutex); 
}

void release(int signum) {
    printf("Releasing semaphore and closing program. %d\n", signum);
    sem_post(mutex);
    shmdt(pool);
    exit(0);
}

int main(int argc, char *argv[]) {

    for (int i = 1; i < NSIG; i++) {
        signal(i, SIG_IGN);
    }
    
    srand(time(NULL));
    signal(SIGINT, release);

    if (argc != 3) {
        printf("Invalid number of arguments!\nUse as: TxGen {reward} {sleep time}\n");
        exit(1);
    }

    reward = atoi(argv[1]);
    if (reward > 3 || reward < 1) {
        printf("Invalid number of reward! Put a number between 1 and 3\n");
        exit(1);
    }

    sleep_time = atoi(argv[2]);
    if (sleep_time < 200 || sleep_time > 3000) {
        printf("Invalid sleep time! Put a number between 200 and 3000.\n");
        exit(1);
    }

    empty = sem_open("EMPTY", 0);
    if (empty == SEM_FAILED) {
        perror("Failure opening the semaphore empty");
        exit(1);
    }

    mutex = sem_open("MUTEX", 0);
    if (mutex == SEM_FAILED) {
        perror("Failure opening the semaphore MUTEX");
        exit(1);
    }

    shmkey_transaction_pool = ftok(".", 65);
    if (shmkey_transaction_pool == (key_t)-1) {
        perror("IPC error: ftok");
        exit(1);
    }

    shmid_transaction = shmget(shmkey_transaction_pool, 0, 0700);
    if (shmid_transaction < 1) {
        perror("Error opening shared memory!\n");
        exit(1);
    }

    pool = (Transaction_Pool *)shmat(shmid_transaction, NULL, 0);
    if (pool == (Transaction_Pool *)-1) {
        perror("Error attaching shared memory!\n");
        exit(1);
    }
    
    while(1){
        transaction_maker(reward);
        usleep(sleep_time * 1000);
    }

    return 0;
}
