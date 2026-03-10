// Francisco Gouveia 2023214517
//  João Canais 2023213000

#ifndef STATISTICS_H
#define STATISTICS_H

#include "controller.h" // For Config, Block, Transactions definitions

typedef struct {
    int total_validated_blocks;
    int total_valid_blocks;
    int total_invalid_blocks;
    int blocks_in_blockchain;
} Statistics;

typedef struct {
    int id;
    int total_reward;
    int success_blocks;
    int failed_blocks;
} Miner_stats;

// Payload for fixed data part of the message
typedef struct {
    int validity_status;
    int miner_id;
    int block_size;
} BlockStatsFixedPayload;

extern Statistics statistics;

// Function prototypes
void write_statistics_console(Statistics *statistics, Miner_stats *miner_thread);
void read_message_queue(); // Will use a globally or locally allocated buffer
void handle_sigusr1(int signum); // Assuming this is the SIGUSR1 handler for statistics
int main_statistics();

#endif
