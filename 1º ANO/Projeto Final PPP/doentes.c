#include "main.h"

pLista cria() {
    pLista aux = (pLista)malloc(sizeof(struct noLista));
    if (aux != NULL) {
        aux->pessoa_info.ID = 0;
        aux->lista_registo = NULL;
        aux->prox = NULL;
    }
    return aux;
}

int vazia(pLista lista) {
    return (lista->prox == NULL);
}

pLista destroi(pLista lista) {
    pLista temp_ptr;
    while (!vazia(lista)) {
        temp_ptr = lista;
        lista = lista->prox;
        if(temp_ptr->lista_registo != NULL){
            destroi_registo(temp_ptr->lista_registo);
        }
        free(temp_ptr);
    }
    free(lista);
    return NULL;
}

void procura(pLista lista, char *chave, pLista *ant, pLista *actual) {
    //int i = 0;
    //char *chave2 = (char *)malloc(MAX * sizeof(char));
    *ant = lista;
    *actual = lista->prox;
    /*
    while (chave[i] != '\0') {
        chave2[i] = tolower(chave[i]);
        i++;
    }
    */
    while (*actual != NULL && strcmp((*actual)->pessoa_info.nome, chave) < 0) {
        *ant = *actual;
        *actual = (*actual)->prox;
    }
    if (*actual != NULL && strcmp((*actual)->pessoa_info.nome, chave) != 0) {
        *actual = NULL;
    }
}

void insere(pLista lista, Registo info, pListaRegisto registo) {
    pLista novo, ant, inutil;
    novo = (pLista)malloc(sizeof(struct noLista));
    if (novo != NULL) {
        novo->pessoa_info = info;
        novo->lista_registo = registo;
        procura(lista, info.nome, &ant, &inutil);
        novo->prox = ant->prox;
        ant->prox = novo;
    }else{
        printf("Erro no sistema");
        return;
    }
}


pLista pesquisa(pLista lista, int id) {
    pLista aux = lista->prox;
    while (aux != NULL) {
        if (aux->pessoa_info.ID == id) {
            return aux;
        }
        aux = aux->prox;
    }
    return NULL;
}

void registo(pLista *lista, Registo info) {

    pListaRegisto lista_registo = cria_registo(); 
    insere(*lista, info, lista_registo); 
}

void pedir_informacao_registo(pLista *lista, int *id_atual){
    Registo info;
    int valor;

    info.ID = ++(*id_atual);

    do{
        printf("Data de nascimento (dd/mm/aa): ");
        valor = scanf("%d/%d/%d", &info.dia, &info.mes, &info.ano);
        if(valor != 3) {
            while(getchar() != '\n');
        }
    }while(verificar_data(info.dia, info.mes, info.ano) || valor != 3);
    getchar();

    do{
        printf("Nome: ");
        fgets(info.nome, MAX, stdin);
    }while(verificar_nome(info.nome));

    info.nome[strlen(info.nome) -1 ] = '\0';

    char cartao[MAX];
    do{
        printf("Cartão de cidadão (XXXXXXXX-X-XXX): ");
        fgets(cartao, MAX, stdin);
        cartao[strlen(cartao) - 1] = '\0';
    }while(verificar_bi(cartao));

    strcpy(info.cartao_cidadao, cartao);

    do {
        printf("Telefone: ");
        if (scanf("%d", &info.telefone) != 1 || info.telefone < 100000000 || info.telefone > 999999999) {
            printf("Telefone inválido. Por favor, insira um número de 9 dígitos.\n");
            while (getchar() != '\n');
        }
    } while (info.telefone < 100000000 || info.telefone > 999999999);
    getchar();

    do{
        printf("Email: ");
        fgets(info.email, MAX, stdin);
    }while(verificar_email(info.email));

    registo(lista, info);
    printf("Paciente registado!\n");
    sleep(2);
    system("clear");
    menu(lista, id_atual);
}

void remover_paciente(pLista *lista, int *id_atual) {
    int id;
    id = pedir_id();
    
    pLista ant = NULL;
    pLista aux = *lista;
    
    while (aux != NULL) {
        if (aux->pessoa_info.ID == id) {
            if (ant == NULL) {
                *lista = aux->prox;
            } else {
                ant->prox = aux->prox;
            }
            if (aux->lista_registo != NULL) {
                destroi_registo(aux->lista_registo);
            }
            free(aux);
            printf("Paciente removido\n");
            break;
        }
        ant = aux;
        aux = aux->prox;
    }
    
    if (aux == NULL) {
        printf("Paciente com ID %d não encontrado.\n", id);
    }
    
    sleep(1.5);
    system("clear");
    menu(lista, id_atual);
}

void imprime(pLista lista, int *id_atual) {
    pLista aux = lista->prox;
    if(aux == NULL){
        printf("Sem pacientes registados\n");
    }else{
        printf("Lista de pacientes\n");
        printf("     ID  ||    NOME\n");
        while (aux) {
            printf("%8d || %s\n", aux->pessoa_info.ID, aux->pessoa_info.nome);
            aux = aux->prox;
        }
    }
    voltar();
    menu(&lista, id_atual);
}