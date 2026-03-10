#include <stdio.h>
#include <stdlib.h> // Necessário para malloc e free
#include <time.h>

#include "keys.c"

#define TIMES 3

void create_arrays(int *arr_A, int *arr_B, int *arr_C, int size){
    keys_A(arr_A, size);
    keys_B(arr_B, size);
    keys_C(arr_C, size);
}

void insertion_sort(int *arr,  int SIZE){
    int temp;
    for(int i = 1; i < SIZE; i++){
        for(int j = i - 1; j >= 0; j--){
            if(arr[j + 1] < arr[j]){
                temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }else{
                break;
            }
        }
    }
}

void max_heap(int i, int *arr, int SIZE){
    int left_child = 2 * i + 1;
    int right_child = 2 * i + 2;
    int largest = i;

    if(left_child < SIZE && arr[left_child] > arr[largest]){
        largest = left_child;
    }
    if(right_child < SIZE && arr[right_child] > arr[largest]){
        largest = right_child;
    }   
    if(largest != i){
        int temp = arr[i];
        arr[i] = arr[largest];
        arr[largest] = temp;
        max_heap(largest, arr, SIZE);
    }
}

void heap_sort(int *arr, int SIZE){

    for(int i = SIZE / 2 - 1; i >= 0; i--){
        max_heap(i, arr, SIZE);
    }

    for(int i = SIZE - 1; i > 0; i--){
        int temp = arr[0];
        arr[0] = arr[i];
        arr[i] = temp;
        max_heap(0, arr, i);
    }

}

void swap(int *a, int *b){
    int temp = *a;
    *a = *b;
    *b = temp;
}

#define QUICK_SORT_CUTOFF 30

void quick_sort(int *arr, int size){
    if (size <= 1) {
        return;
    }
  
    if (size <= QUICK_SORT_CUTOFF) {
        insertion_sort(arr, size);
        return;
    }

    int pivot_val;
    int i = 0;
    int j = size - 1;

    if (size > 2) {
        int mid_idx = (size - 1) / 2; // Middle index for arr[0...size-1]

        // Sort arr[0], arr[mid_idx], arr[size-1] to find the median
        if (arr[0] > arr[mid_idx]) {
            swap(&arr[0], &arr[mid_idx]);
        }
        if (arr[0] > arr[size - 1]) {
            swap(&arr[0], &arr[size - 1]);
        }
        if (arr[mid_idx] > arr[size - 1]) {
            swap(&arr[mid_idx], &arr[size - 1]);
        }
        // Now arr[mid_idx] holds the median of the three values.
        pivot_val = arr[mid_idx];
    } else {
        // Fallback for size = 2 (CUTOFF usually handles this, but as a safeguard)
        pivot_val = arr[size / 2];
    }
    
    int current_i = i;
    int current_j = j;
    
    while(current_i <= current_j){
        // 3. Efficient handling of elements equal to pivot (inherent in Hoare partition)
        while(arr[current_i] < pivot_val){
            current_i++;
        }

        while(arr[current_j] > pivot_val){
            current_j--;
        }
        
        if(current_i <= current_j){
            swap(&arr[current_i], &arr[current_j]);
            current_i++;
            current_j--;
        }   
    }
         
    // Recursive calls on the two partitions
    // Left partition: arr[0...current_j]
    // Size of left partition: current_j + 1
    if (current_j > 0) { // If there's a left partition with at least one element (original was j > 0)
        quick_sort(arr, current_j + 1);
    }

    // Right partition: arr[current_i...size-1]
    // Starts at arr + current_i, size is size - current_i
    if (current_i < size) { // If there's a right partition
        quick_sort(arr + current_i, size - current_i);
    }
        
}

int main(){

    int values[] = {10000,30000, 50000, 60000, 70000, 80000, 100000, 150000, 200000, 250000, 300000, 350000, 400000, 500000, 1000000};
    srand(time(NULL));
    clock_t start;

    for(int l = 0; l < TIMES; l++){
    
        printf("--- Iteration %d ---\n", l + 1);
        for(int k = 0; k < (int)(sizeof(values)/sizeof(int)) ; k++){

            printf("Size: %d\n", values[k]);

            // Alocar arrays dinamicamente na heap
            int *arr_A = (int*)malloc(values[k] * sizeof(int));
            int *arr_B = (int*)malloc(values[k] * sizeof(int));
            int *arr_C = (int*)malloc(values[k] * sizeof(int));

            // Verificar se a alocação foi bem-sucedida
            if (arr_A == NULL || arr_B == NULL || arr_C == NULL) {
                fprintf(stderr, "Memory allocation failed for size %d\n", values[k]);
                // Liberar memória que possa ter sido alocada com sucesso antes de continuar/sair
                if (arr_A != NULL) free(arr_A);
                if (arr_B != NULL) free(arr_B);
                if (arr_C != NULL) free(arr_C);
                continue; // Pula para o próximo tamanho de array ou próxima iteração de TIMES
            }

            create_arrays(arr_A, arr_B, arr_C, values[k]);

            if (k < 10){ // Limita o insertion_sort para tamanhos menores
                // Teste Insertion Sort para arr_A
                create_arrays(arr_A, arr_B, arr_C, values[k]); // Garante dados frescos para arr_A
                start = clock();
                insertion_sort(arr_A, values[k]);
                printf("Insertion Sort A: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);

                // Teste Insertion Sort para arr_B
                create_arrays(arr_A, arr_B, arr_C, values[k]); // Garante dados frescos para arr_B
                start = clock();
                insertion_sort(arr_B, values[k]);
                printf("Insertion Sort B: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);

                // Teste Insertion Sort para arr_C
                create_arrays(arr_A, arr_B, arr_C, values[k]); // Garante dados frescos para arr_C
                start = clock();
                insertion_sort(arr_C, values[k]);
                printf("Insertion Sort C: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);
                printf("\n");
            }

            // Teste Heap Sort
            create_arrays(arr_A, arr_B, arr_C, values[k]);
            start = clock();
            heap_sort(arr_A, values[k]);
            printf("Heap Sort A: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);

            create_arrays(arr_A, arr_B, arr_C, values[k]);
            start = clock();
            heap_sort(arr_B, values[k]);
            printf("Heap Sort B: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);

            create_arrays(arr_A, arr_B, arr_C, values[k]);
            start = clock();
            heap_sort(arr_C, values[k]);
            printf("Heap Sort C: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);
            printf("\n");

            // Teste Quick Sort
            create_arrays(arr_A, arr_B, arr_C, values[k]);
            start = clock();
            quick_sort(arr_A, values[k]);
            printf("Quick Sort A: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);
            
            create_arrays(arr_A, arr_B, arr_C, values[k]);
            start = clock();
            quick_sort(arr_B, values[k]);
            printf("Quick Sort B: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);
            
            create_arrays(arr_A, arr_B, arr_C, values[k]);
            start = clock();
            quick_sort(arr_C, values[k]);
            printf("Quick Sort C: %f s\n", (double)(clock() - start) / CLOCKS_PER_SEC);
            printf("\n\n");

            // Liberar a memória alocada para evitar vazamentos de memória
            free(arr_A);
            free(arr_B);
            free(arr_C);
        }
    }
    return 0;
}