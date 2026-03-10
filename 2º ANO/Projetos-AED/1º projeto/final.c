#include <stdio.h>
#include <stdlib.h>
#include <time.h>


int compare(const void* a, const void* b) {
    return (*(int*)a - *(int*)b);
 }

int solucao_um(int *lista, int n);
int solucao_dois(int *lista, int n);
long int solucao_tres(int *lista, int n);

void shuffle(int *array, int n);
void mostrar_lista(int *lista, int n);

int main(){

    int lista[10] = {1000000, 2000000,3000000,5000000,6000000,8000000,9000000,10000000,12000000,14000000};

    FILE *arquivo = fopen("resultados7.txt", "a");

    srand(time(NULL));
    
    int tamanho = sizeof(lista)/sizeof(int);
    int iterecao = 15;

    fprintf(arquivo, "%d\n", iterecao);
    
    for (int j = 0; j < iterecao; j++){

        for(int k = 0; k < tamanho; k++){
            printf("---------------------------------------\n");
            printf("Tamanho da lista: %d\n", lista[k]);

            int *lista_valores = (int *)malloc(lista[k] * sizeof(int));

            if(lista_valores == NULL){
                printf("Erro ao alocar memoria\n");
                return 1;
            }

            for(int i = 0; i < lista[k]; i++){
                lista_valores[i] = i;
            }

            //mostrar_lista(lista_valores, lista[0]);

            int index = rand() % lista[k] - 1;

            printf("Valor removido: %d\n\n", lista_valores[index]);

            for(int i = index; i < lista[k]; i++){
                lista_valores[i] = lista_valores[i] + 1;
            }

            lista_valores = realloc(lista_valores, (lista[k] - 1) * sizeof(int));

            shuffle(lista_valores, lista[k]);

            //mostrar_lista(lista_valores, lista[0] - 1);
            //clock_t primeiro = clock();
            //printf("Solucao 1: %d\n", solucao_um(lista_valores, lista[k]));
            //printf("Tempo: %f s\n\n", (double)(clock() - primeiro) / CLOCKS_PER_SEC);
            //fprintf(arquivo, "%d %f\n", lista[k], (double)(clock() - primeiro) / CLOCKS_PER_SEC);

            clock_t segundo = clock();
            printf("Solucao 2: %d\n", solucao_dois(lista_valores, lista[k]));
            printf("Tempo: %f s\n\n", (double)(clock() - segundo) / CLOCKS_PER_SEC);
            fprintf(arquivo, "%d %f\n", lista[k], (double)(clock() - segundo) / CLOCKS_PER_SEC);

            clock_t terceiro = clock();
            printf("Solucao 3: %ld\n", solucao_tres(lista_valores, lista[k]));
            printf("Tempo: %f s\n\n", (double)(clock() - terceiro) / CLOCKS_PER_SEC);
            fprintf(arquivo, "%d %f\n", lista[k], (double)(clock() - terceiro) / CLOCKS_PER_SEC);

            printf("---------------------------------------\n");
            free(lista_valores);
        }
    }

    fclose(arquivo);

    return 0;
}

void mostrar_lista(int *lista, int n){
    for (int i = 0; i < n; i++){
        printf("%d ", lista[i]);
    }
    printf("\n");
}

void shuffle(int *array, int n){
    srand( time(NULL) );

    for (int i = 0; i < n; i++){
        int index_troca = rand() % n;
        int temp = array[i];
        array[i] = array[index_troca];
        array[index_troca] = temp;
    }
}

int solucao_um(int *lista, int n){
    for (int i = 0; i< n; i++){
        for (int j = 0; i < n -1 ; j++){
            if (i == lista[j]){
                break;
            }
            else if ((i != lista[j]) && (j == n - 1)){
                return i;
            }
        }
    }
    return -1;
}

int solucao_dois(int *lista, int n){
    qsort(lista, n, sizeof(int), compare);

    for (int i = 0; i <n - 1; i++){
        if(lista[i + 1] - lista[i] != 1){
            return lista[i] + 1;
        }
    }

    return -1;
}


long int solucao_tres(int *lista, int n){

    long int max = lista[0];
    long int min = lista[0];

    long int soma_real = 0;

    for (int i = 0; i < n; i++){
        soma_real += lista[i];
        if (lista[i] < min){
            min = lista[i];
        }
        if (lista[i] > max){
            max = lista[i];
        }
    }

    long int soma_espectavel = (max * (max + 1)) / 2 - (min * (min - 1)) / 2;

    return soma_espectavel - soma_real;
}