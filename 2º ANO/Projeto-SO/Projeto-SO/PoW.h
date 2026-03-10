// Francisco Gouveia 2023214517
//  João Canais 2023213000
#ifndef POW_H
#define POW_H

#include "miner.h"

#define POW_MAX_OPS 10000000

typedef struct {
  char hash[HASH_SIZE];
  double elapsed_time;
  int operations;
  int error;
} PoWResult;

void compute_sha256(const Block *input, char *output);
PoWResult proof_of_work(Block *block);
enum difficulty_level get_difficulty_level(const Block *block);
int verify_nonce(Block *block);

#endif
