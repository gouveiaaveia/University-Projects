#include <stdio.h>
#include <stdlib.h>
#include <time.h>


int compare(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

void shuffle(int *arr, int size) {
    for (int i = size - 1; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }
}

void add_repeated_elements(int *arr, int SIZE, int repeat_count) {
    long pos_to_replace = SIZE - repeat_count;
    for (int i = 0; i < repeat_count; i++) {
        int pos_to_duplicate = rand() % SIZE;
        arr[pos_to_replace] = arr[pos_to_duplicate];
        pos_to_replace++;
    }
}

void keys_A(int *arr, int SIZE) {
    int repeat_count = SIZE * 0.05;
    for (int i = 0; i < SIZE - repeat_count; i++) {
        arr[i] = i;
    }
    add_repeated_elements(arr, SIZE, repeat_count);
    qsort(arr, SIZE, sizeof(int), compare);
}

void keys_B(int *arr, int SIZE) {
    int temp[SIZE];
    keys_A(temp, SIZE);
    for(int i = 0; i < SIZE; i++){
        arr[i] = temp[SIZE - i - 1];
    }
}

void keys_C(int *arr, int SIZE) {
    keys_A(arr, SIZE);
    shuffle(arr, SIZE);
}