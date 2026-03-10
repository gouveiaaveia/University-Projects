// Francisco Gouveia 2023214517
//  João Canais 2023213000

#include "controller.h"
#include "statistics.h"
#include "miner.h"

Miner_stats *miner_stats;
int s=1;
key_t key_msg;
int mqid_msg;

void *msgrcv_buffer_storage = NULL;
size_t msgrcv_buffer_data_capacity = 0; 

void read_message_queue() {

    if (!msgrcv_buffer_storage || msgrcv_buffer_data_capacity == 0) {
        fprintf(stderr, "Statistics: Receive buffer not initialized or zero capacity.\n");
        return;
    }

    ssize_t actual_msg_data_len;

    actual_msg_data_len = msgrcv(mqid_msg, msgrcv_buffer_storage, msgrcv_buffer_data_capacity, 1, IPC_NOWAIT);

    if (actual_msg_data_len != -1) {

        char *received_data_ptr = (char*)msgrcv_buffer_storage + sizeof(long);

        if ((size_t)actual_msg_data_len < sizeof(BlockStatsFixedPayload)) {
            fprintf(stderr, "Statistics: Received message too short for fixed payload. Len: %zd. Skipping.\n", actual_msg_data_len);
            return;
        }

        BlockStatsFixedPayload *fixed_payload_ptr = (BlockStatsFixedPayload *)received_data_ptr;

        int received_miner_id = fixed_payload_ptr->miner_id;
        int received_block_size = fixed_payload_ptr->block_size;
        int received_validity_status = fixed_payload_ptr->validity_status;
        
        Transactions *received_transactions_ptr = (Transactions *)(received_data_ptr + sizeof(BlockStatsFixedPayload));

        if (received_miner_id < 0 || received_miner_id >= config.NUM_MINERS) {
            fprintf(stderr, "Statistics: Received invalid miner_id %d. Max miners: %d. Skipping.\n", 
                    received_miner_id, config.NUM_MINERS);
            return;
        }
        
        size_t expected_total_data_len = sizeof(BlockStatsFixedPayload) + (size_t)received_block_size * sizeof(Transactions);
        if (received_block_size < 0 || (size_t)actual_msg_data_len != expected_total_data_len) {
             fprintf(stderr, "Statistics: Received message data length mismatch (expected %zu, got %zd) or invalid block_size %d for miner_id %d. Skipping.\n",
                     expected_total_data_len, actual_msg_data_len, received_block_size, received_miner_id);
            return;
        }

        if (received_validity_status == 1) {
            statistics.total_valid_blocks++;
            statistics.blocks_in_blockchain++;
            statistics.total_validated_blocks++;
            miner_stats[received_miner_id].success_blocks++;

            for (int i = 0; i < received_block_size; i++) {
                miner_stats[received_miner_id].total_reward += received_transactions_ptr[i].reward;
            }        
        } else {
            statistics.total_invalid_blocks++;
            statistics.total_validated_blocks++;
            miner_stats[received_miner_id].failed_blocks++;
        }
    } else {
        if (errno != ENOMSG) {
            perror("Statistics: msgrcv error in read_message_queue");
        }
    }
}

void print_statistics(Statistics *statistics) {
    char log_message[2048];
    int offset = 0;

    offset += snprintf(log_message + offset, sizeof(log_message) - offset,
        "\n=================== Statistics ===================\n");
    offset += snprintf(log_message + offset, sizeof(log_message) - offset,
        "Total valid blocks: %d\n", statistics->total_valid_blocks);
    offset += snprintf(log_message + offset, sizeof(log_message) - offset,
        "Total invalid blocks: %d\n", statistics->total_invalid_blocks);
    offset += snprintf(log_message + offset, sizeof(log_message) - offset,
        "Total blocks in blockchain: %d\n", statistics->blocks_in_blockchain);
    offset += snprintf(log_message + offset, sizeof(log_message) - offset,
        "Total blocks validated: %d\n", statistics->total_validated_blocks);

    for (int i = 0; i < config.NUM_MINERS; i++) {
        offset += snprintf(log_message + offset, sizeof(log_message) - offset,
            "Miner %d - Total Reward: %d, Success Blocks: %d, Failed Blocks: %d\n",
            miner_stats[i].id,
            miner_stats[i].total_reward,
            miner_stats[i].success_blocks,
            miner_stats[i].failed_blocks);
    }

    offset += snprintf(log_message + offset, sizeof(log_message) - offset,
        "===================================================\n");

    log_event(log_message, NULL);
}

void handle_signals_statistics(int signum) {
    if (signum == SIGUSR1) {
        print_statistics(&statistics);
    } else if (signum == SIGINT) {
        s = 0;
    }
}

int main_statistics() {

    for (int i = 1; i < NSIG; i++) {
        signal(i, SIG_IGN);
    }

    msgrcv_buffer_data_capacity = sizeof(BlockStatsFixedPayload) + (size_t)config.TRANSACTION_PER_BLOCK * sizeof(Transactions);
 
    size_t total_msgrcv_buffer_size = sizeof(long) + msgrcv_buffer_data_capacity;
    msgrcv_buffer_storage = malloc(total_msgrcv_buffer_size);

    if (!msgrcv_buffer_storage) {
        perror("Statistics: Failed to allocate memory for receive buffer");
        exit(1);
    }

    signal(SIGUSR1, handle_signals_statistics);
    signal(SIGINT, handle_signals_statistics);

    miner_stats = malloc(sizeof(Miner_stats) * config.NUM_MINERS);
    if (miner_stats == NULL) {
        perror("Error allocating memory for miner statistics");
        free(msgrcv_buffer_storage); 
        exit(1);
    }

    for (int i = 0; i < config.NUM_MINERS; i++) {
        miner_stats[i].id = i;
        miner_stats[i].total_reward = 0;
        miner_stats[i].success_blocks = 0;
        miner_stats[i].failed_blocks = 0;
    }

    statistics.total_valid_blocks = 0;
    statistics.total_invalid_blocks = 0;
    statistics.blocks_in_blockchain = 0;

    key_msg = ftok(".", 67); 
    if (key_msg == (key_t)-1) {
        perror("Error generating key for message queue");
        free(miner_stats);
        free(msgrcv_buffer_storage);
        exit(1);
    }

    mqid_msg = msgget(key_msg, 0777);
    if (mqid_msg == -1) {
        perror("msgget");
        free(miner_stats);
        free(msgrcv_buffer_storage);
        exit(1);
    }

    s = 1;
    while (s) {
        read_message_queue();
        usleep(100000); 
    }
    
    free(miner_stats);
    free(msgrcv_buffer_storage);
    printf("Statistics process terminating.\n");
    
    return 0;
}
