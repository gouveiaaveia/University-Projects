// Francisco Gouveia 2023214517
//  João Canais 2023213000

#include "miner.h"
#include "PoW.h"

#include <openssl/sha.h>


enum difficulty_level get_difficulty_level(const Block *block) {
    int max_reward = 0;

    if(block == NULL) {
        return EMPTY;
    }

    for (int i = 0; i < block->size; i++) {
        if(block->transactions[i].reward > max_reward) {
            max_reward = block->transactions[i].reward;
        }
    }

    if(max_reward >= 3) { //change this to 4 in the future
        return HIGH;
    } else if(max_reward >= 2) {
        return MEDIUM;
    } else {
        return LOW;
    }
}

unsigned char *serialize_block(const Block *block, size_t *sz_buf) {
    
    *sz_buf = sizeof(long) +                                 // block->id
              HASH_SIZE +                                    // previous_hash
              sizeof(time_t) +                               // timestamp
              block->size * sizeof(Transactions) +           // transactions
              sizeof(unsigned int);                          // nonce

    unsigned char *buffer = malloc(*sz_buf);
    if (!buffer) {
        fprintf(stderr, "Error: Failed to allocate memory for block serialization.\n");
        return NULL;
    }

    unsigned char *p = buffer;

    memcpy(p, &block->id, sizeof(long));
    p += sizeof(long);

    memcpy(p, block->previous_hash, HASH_SIZE);
    p += HASH_SIZE;

    memcpy(p, &block->timestamp, sizeof(time_t));
    p += sizeof(time_t);

    for (int i = 0; i < block->size; ++i) {
        memcpy(p, &block->transactions[i], sizeof(Transactions));
        p += sizeof(Transactions);
    }

    memcpy(p, &block->nonce, sizeof(unsigned int));
    p += sizeof(unsigned int);

    return buffer;
}

void compute_sha256(const Block *block, char *output) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    size_t buffer_sz;

    //debug
    //printf("Computing hash for block: ID=%ld, nonce=%u, prev_hash=%.10s\n", block->id, block->nonce, block->previous_hash);

    unsigned char *buffer = serialize_block(block, &buffer_sz);
    if (!buffer) {
        fprintf(stderr, "Error: Failed to serialize block for SHA256 computation.\n");
        return;
    }

    SHA256(buffer, buffer_sz, hash);
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        sprintf(output + (i * 2), "%02x", hash[i]);
    }
    output[SHA256_DIGEST_LENGTH * 2] = '\0';

    //debug
    //printf("Generated hash: %.10s... for block ID=%ld\n", output, block->id);
    free(buffer);
}

int check_difficulty(const Block *block, const char *hash) {
    int minimum = 3;
  
    int zeros = 0;
    enum difficulty_level difficulty = get_difficulty_level(block);
  
    while (hash[zeros] == '0') {
      zeros++;
    }
  
    if (zeros < minimum) return 0;
  
    char next_char = hash[zeros];
  
    switch (difficulty) {
      case LOW:
        if ((zeros == 4 && next_char <= 'b') || zeros > 4) return 1;
        break;
      case MEDIUM:
        if (zeros >= 5) return 1;
        break;
      case HIGH:
        if ((zeros == 6 && next_char <= 'b') || zeros > 6) return 1;
        break;
      default:
        fprintf(stderr, "Invalid Difficult\n");
        exit(2);
    }
  
    return 0;
  }

PoWResult proof_of_work(Block *block) {
    PoWResult result;
  
    result.elapsed_time = 0.0;
    result.operations = 0;
    result.error = 0;
  
    block->nonce = 0;
  
    char hash[SHA256_DIGEST_LENGTH * 2 + 1];
    clock_t start = clock();
  
    while (1) {
      compute_sha256(block, hash);
  
      if (check_difficulty(block, hash)) {
        result.elapsed_time = (double)(clock() - start) / CLOCKS_PER_SEC;
        strcpy(result.hash, hash);
        return result;
      }
      block->nonce++;
      if (block->nonce > POW_MAX_OPS) {
        fprintf(stderr, "Giving up\n");
        result.elapsed_time = (double)(clock() - start) / CLOCKS_PER_SEC;
        result.error = 1;
        return result;
      }
      result.operations++;
    }
  }

int verify_nonce(Block *block) {
    char hash[SHA256_DIGEST_LENGTH * 2 + 1];
    compute_sha256(block, hash);
    return check_difficulty(block, hash);
}
