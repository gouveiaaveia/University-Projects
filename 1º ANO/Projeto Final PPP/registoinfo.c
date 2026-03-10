#include "main.h"

pListaRegisto cria_registo() {
    pListaRegisto aux = (pListaRegisto)malloc(sizeof(struct noListaRegisto));
    if (aux != NULL) {
        aux->prox = NULL;
    }
    return aux;
}

int vazia_registo(pListaRegisto lista) {
    return (lista->prox == NULL);
}

pListaRegisto destroi_registo(pListaRegisto lista) {
    pListaRegisto temp_ptr;
    while (!vazia_registo(lista)) {
        temp_ptr = lista;
        lista = lista->prox;
        free(temp_ptr);
    }
    free(lista);
    return NULL;
}

void procura_registo(pListaRegisto lista, int chave, pListaRegisto *ant, pListaRegisto *actual) {
    *ant = lista;
    *actual = lista->prox;
    while (*actual != NULL && (*actual)->info.tensao_maxima > chave ) {
        *ant = *actual;
        *actual = (*actual)->prox;
    }
    if (*actual != NULL && (*actual)->info.tensao_maxima != chave) {
        *actual = NULL;
    }
}

void insere_registo(pListaRegisto lista, Info info) {
    pListaRegisto novo, ant, inutil;
    novo = (pListaRegisto)malloc(sizeof(struct noListaRegisto));
    if (novo != NULL) {
        novo->info = info;
        procura_registo(lista, info.tensao_maxima, &ant, &inutil);
        novo->prox = ant->prox;
        ant->prox = novo;
    }
}

pListaRegisto pesquisa_registo(pListaRegisto lista, int id) {
    pListaRegisto aux = lista->prox;
    while (aux != NULL) {
        if (aux->info.id == id) {
            return aux;
        }
        aux = aux->prox;
    }
    return NULL;
}

void registo_medicoes(pLista *lista, pListaRegisto lista2, int id) {

    pLista aux = pesquisa(*lista, id);
    insere_registo(aux->lista_registo, lista2->info);
}

void pedir_medicoes(pLista *lista, int id, int *id_atual) {
    pLista aux = pesquisa(*lista, id);
    pListaRegisto medicao_atual = (struct noListaRegisto *)malloc(sizeof(struct noListaRegisto));

    if (medicao_atual == NULL) {
        printf("Erro na alocação de memória\n");
        return;
    }

    if (aux != NULL) {
        int valor;
        medicao_atual->info.id = id;

        do {
            printf("Data (dd/mm/aa): ");
            valor = scanf("%d/%d/%d", &(medicao_atual->info.dia), &(medicao_atual->info.mes), &(medicao_atual->info.ano));
            if (valor != 3) {
                printf("Formato de data inválido. Tente novamente.\n");
                while (getchar() != '\n'); 
            }
        } while (valor != 3 || verificar_data(medicao_atual->info.dia, medicao_atual->info.mes, medicao_atual->info.ano) || verifica_data_consula_nascimento(aux, medicao_atual));

        do {
            printf("Tensão mínima: ");
            valor = scanf("%d", &(medicao_atual->info.tensao_minima));
            if (valor != 1) {
                printf("Valor inválido. Tente novamente.\n");
                while (getchar() != '\n');
            }
        } while (valor != 1 || verificar_tensao_minima(medicao_atual->info.tensao_minima));

        do {
            printf("Tensão máxima: ");
            valor = scanf("%d", &(medicao_atual->info.tensao_maxima));
            if (valor != 1) {
                printf("Valor inválido. Tente novamente.\n");
                while (getchar() != '\n');
            }
        } while (valor != 1 || verificar_tensao_maxima(medicao_atual->info.tensao_maxima, medicao_atual->info.tensao_minima));

        char *avaliacao = (char *)malloc(MAX * sizeof(char));
        if (avaliacao == NULL){
            printf("Erro na avaliação\n");
            return;
        }

        avaliar_tensao(avaliacao, &(medicao_atual->info.tensao_maxima), &(medicao_atual->info.tensao_minima));
        strcpy(medicao_atual->info.avaliacao_tesao, avaliacao);

        free(avaliacao);

        do {
            printf("Altura (cm): ");
            valor = scanf("%f", &(medicao_atual->info.altura));
            if (valor != 1) {
                printf("Valor inválido. Tente novamente.\n");
                while (getchar() != '\n'); 
            }
        } while (valor != 1 || verificar_altura(medicao_atual->info.altura));

        do {
            printf("Peso (kg): ");
            valor = scanf("%f", &(medicao_atual->info.peso));
            if (valor != 1) {
                printf("Valor inválido. Tente novamente.\n");
                while (getchar() != '\n');
            }
        } while (valor != 1 || verificar_peso(medicao_atual->info.peso));
    } else {
        printf("Paciente com ID %d não encontrado.\n", id);
        voltar();
        menu(lista, id_atual);
    }

    registo_medicoes(lista, medicao_atual, id);
    free(medicao_atual);
    printf("Medições registradas!\n");

    sleep(2);
    system("clear");
    menu(lista, id_atual);
}

void mostrar_informacao(pLista lista, int id, int *id_atual) {
    system("clear"); 
    pLista aux = pesquisa(lista, id);
    if (aux != NULL) {
        printf("ID: %d\n", aux->pessoa_info.ID);
        printf("Nome: %s\n", aux->pessoa_info.nome);
        printf("Data de Nascimento: %d/%d/%d\n", aux->pessoa_info.dia, aux->pessoa_info.mes, aux->pessoa_info.ano);
        printf("Medições:\n");
        pListaRegisto medicao_atual = aux->lista_registo->prox;
        while (medicao_atual != NULL) {
            printf("Data: %d/%d/%d, Tensão Máxima: %d, Tensão Mínima: %d, Altura: %.2f, Peso: %.2f\n",
                   medicao_atual->info.dia, medicao_atual->info.mes, medicao_atual->info.ano,
                   medicao_atual->info.tensao_maxima, medicao_atual->info.tensao_minima,
                   medicao_atual->info.altura, medicao_atual->info.peso);
            medicao_atual = medicao_atual->prox;
        }
        printf("\n");
    } else {
        printf("Paciente com ID %d não encontrado.\n", id);
    }
    voltar();
    menu(&lista, id_atual);
}

