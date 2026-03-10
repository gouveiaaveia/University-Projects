#include "node_struct.h"

#define SIZE 100000

void shuffle(int *arr, int size) {
    for(int i = size - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}

void keys_A(int *arr){
    for(int i = 0; i < SIZE; i++) {
        arr[i] = i / 1.2;
    }
}

void keys_B(int *arr){
    for(int i = SIZE; i > 0; i--) {
        arr[i] = i / 1.2;
    }
}

void keys_C(int *arr){
    for(int i = 0; i < SIZE; i++) {
        arr[i] = i / 1.2;
    }
    shuffle(arr, SIZE);
}

void keys_D(int *arr){
    for(int i = 0; i < SIZE; i++) {
        arr[i] = i / 10;
    }
    shuffle(arr, SIZE);
}