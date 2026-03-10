// Francisco Gouveia 2023214517
//  João Canais 2023213000

#ifndef MINER_H
#define MINER_H

#include "controller.h"

#define INITIAL_HASH \
  "00006a8e76f31ba74e21a092cca1015a418c9d5f4375e7a4fec676e1d2ec1436"

enum difficulty_level {
    LOW,
    MEDIUM,
    HIGH,
    EMPTY
};

typedef struct{
    int id;
}Miner;

extern Miner *miner_thread;

void* mine(void *arg);
void main_miner();

#endif
