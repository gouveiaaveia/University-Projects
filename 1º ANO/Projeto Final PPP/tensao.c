#include "main.h"

pListaTensao cria_tensao() {
    pListaTensao lista = (pListaTensao)malloc(sizeof(struct noListaTensao));
    if (lista != NULL) {
        lista->prox = NULL;
    }
    return lista;
}

int vazia_tensao(pListaTensao lista){
    return(lista->prox == NULL);
}

pListaTensao destroi_tensao(pListaTensao lista) {
    pListaTensao temp_ptr;
    while (!vazia_tensao(lista)) {
        temp_ptr = lista;
        lista = lista->prox;
        free(temp_ptr);
    }
    free(lista);
    return NULL;
}

void procura_tensao(pListaTensao lista, pLista *aux, pListaTensao *ant, pListaTensao *actual) {
    pLista chave = (*aux);
    *ant = lista;
    *actual = lista->prox;
    while (*actual != NULL && (*actual)->tensao_alta->lista_registo->info.tensao_maxima > chave->lista_registo->info.tensao_maxima) {
        *ant = *actual;
        *actual = (*actual)->prox;
    }
    if (*actual != NULL && (*actual)->tensao_alta->lista_registo->info.tensao_maxima != chave->lista_registo->info.tensao_maxima) {
        *actual = NULL;
    }
}

void insere_tensao(pListaTensao lista, pLista info) {
    pListaTensao novo, ant, inutil;
    novo = (pListaTensao)malloc(sizeof(struct noListaTensao));
    if (novo != NULL) {
        novo->tensao_alta = info;
        procura_tensao(lista, &info, &ant, &inutil);
        novo->prox = ant->prox;
        ant->prox = novo;
    }   
}


void imprime_tensao(pListaTensao lista) {
    pListaTensao aux = lista->prox;
    printf("||  ID    ||  NOME       ||   Tensão Máxima  ||   Tensão Mínima  ||  Avaliação         ||  Data\n");
    while (aux != NULL) {
        pListaRegisto primeiro_registo = aux->tensao_alta->lista_registo->prox;
        printf("||  %-6d||  %-10s||  %-15d||  %-15d||  %-20s||  %d/%d/%d\n",
                primeiro_registo->info.id, aux->tensao_alta->pessoa_info.nome,
                primeiro_registo->info.tensao_maxima, primeiro_registo->info.tensao_minima,
                primeiro_registo->info.avaliacao_tesao, primeiro_registo->info.dia,
                primeiro_registo->info.mes, primeiro_registo->info.ano);
        aux = aux->prox;
    }
}

void tensao_maxima(pLista lista, int *id_atual) {
    int valor_tensao;
    pLista aux_paciente = lista->prox;
    pListaTensao lista_tensao = cria_tensao();
    
    if(lista_tensao == NULL){
        printf("Erro ao criar lista de tensão\n");
        return;
    }

    printf("Valor de tensão máxima: ");
    scanf("%d", &valor_tensao);
    
    if(aux_paciente == NULL ) {
        printf("Sem informação de pacientes\n");
        voltar();
        menu(&lista, id_atual);
        return;
    }
    
    while(aux_paciente != NULL) {
        if(aux_paciente->lista_registo != NULL) {
            // Apenas acessa o primeiro registo
            pListaRegisto primeiro_registo = aux_paciente->lista_registo->prox;
            if (primeiro_registo != NULL && primeiro_registo->info.tensao_maxima >= valor_tensao) {
                insere_tensao(lista_tensao, aux_paciente);
            } else {
                printf("Paciente sem registos\n");
            }
        } else {
            printf("Paciente sem registos\n");
        }
        // Avança para o próximo paciente
        aux_paciente = aux_paciente->prox;
    }

    // Retorna ao menu principal
    imprime_tensao(lista_tensao);
    destroi_tensao(lista_tensao);
    voltar();
    menu(&lista, id_atual);
}


void pacientes_tensao_alta(pLista lista, int *id_atual){
    pLista aux_paciente = lista->prox;
    pListaTensao lista_tensao = cria_tensao();
    
    if(lista_tensao == NULL){
        printf("Erro ao criar lista de tensão\n");
        return;
    }
    
    while(aux_paciente != NULL) {
        if(aux_paciente->lista_registo != NULL) {
            pListaRegisto aux_registo = aux_paciente->lista_registo->prox;
            if (aux_registo != NULL && aux_registo->info.tensao_maxima >= 140) {
                insere_tensao(lista_tensao, aux_paciente);
            }
        } else {
            printf("Paciente sem registos\n");
        }
        aux_paciente = aux_paciente->prox;
    }
    imprime_tensao(lista_tensao);
    printf("\n");
    // Destruir a lista para ser reutilizada quando necessário
    destroi_tensao(lista_tensao);
    voltar();
    menu(&lista, id_atual);
}


//avaliação da tensão
void avaliar_tensao(char *avaliacao, int *maxima, int *minima) {
    if ((*maxima > HIPERTENSAO_I_MAXIMA_m && *maxima < HIPERTENSAO_I_MAXIMA_M) ||
        (*minima > HIPERTENSAO_I_MINIMA_m && *minima < HIPERTENSAO_I_MINIMA_M)) {
        strcpy(avaliacao, "Hipertensão grau 1");
    } else if ((*maxima > HIPERTENSAO_II_MAXIMA_m && *maxima < HIPERTENSAO_II_MAXIMA_M) ||
               (*minima > HIPERTENSAO_II_MINIMA_m && *minima < HIPERTENSAO_II_MINIMA_M)) {
        strcpy(avaliacao, "Hipertensão grau 2");
    } else if (*maxima >= HIPERTENSAO_III_MAXIMA || *minima >= HIPERTENSAO_III_MINIMA) {
        strcpy(avaliacao, "Hipertensão grau 3");
    } else if (*maxima >= HIPERTENSAO_SISTOLICA_ISOLADA_MAXIMA && *minima < HIPERTENSAO_SISTOLICA_ISOLADA_MINIMA) {
        strcpy(avaliacao, "Hipertensão sistólica isolada");
    } else if(*maxima < TENSAO_OTIMA_M || *minima < TENSAO_OTIMA_m) {
        strcpy(avaliacao, "Ótima");
    }else if((*maxima > TENSAO_NORMAL_MAXIMA_m && *maxima < TENSAO_NORMAL_MAXIMA_M) ||
        (*minima > TENSAO_NORMAL_MINIMA_m && *minima < TENSAO_NORMAL_MINIMA_M)){
        strcpy(avaliacao, "Normal");
    }else if((*maxima > TENSAO_NORMAL_ALTA_MAXIMA_m && *maxima < TENSAO_NORMAL_ALTA_MAXIMA_M) ||
        (*minima > TENSAO_NORMAL_ALTA_MINIMA_m && *minima < TENSAO_NORMAL_ALTA_MINIMA_M)){
        strcpy(avaliacao, "Normal Alta");
    }else{
        strcpy(avaliacao,"Medição Inválida");
    }
}