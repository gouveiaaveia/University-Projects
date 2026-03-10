#include "main.h"

int verificar_data(int dia, int mes, int ano) {
    if (mes <= 12 && ano > 1901) {
        if (mes == 4 || mes == 6 || mes == 9 || mes == 11) {
            if (dia > 30 || dia < 1) {
                printf("Data Inválida\n");
                return 1;
            }
        }
        else if (mes == 2) {
            if ((ano % 4 == 0 && ano % 100 != 0) || (ano % 400 == 0)) {
                if (dia > 29 || dia < 1) {
                    printf("Data Inválida\n");
                    return 1;
                }
            }
            else {
                if (dia > 28 || dia < 1) {
                    printf("Data Inválida\n");
                    return 1;
                }
            }
        }
        else {
            if (dia > 31 || dia < 1) {
                printf("Data Inválida\n");
                return 1;
            }
        }
    } else {
        printf("Data Inválida\n");
        return 1;
    }
    return 0;
}


int verifica_data_consula_nascimento(pLista lista, pListaRegisto registo){
    if((lista->pessoa_info.ano > registo->info.ano) || ((lista->pessoa_info.ano == registo->info.ano) && (lista->pessoa_info.mes > registo->info.mes))
        || ((lista->pessoa_info.ano == registo->info.ano) && (lista->pessoa_info.mes == registo->info.mes) && (lista->pessoa_info.dia > registo->info.dia))){
            printf("Data inválida, introduza uma data posterior à data de nascimento\n");
            return 1;
        }
    return 0;
}

int verificar_nome(char *nome){
    int i = 0;
    while(nome[i] != '\n'){
        if((nome[i] < 'a' && nome[i] < 'A') || (nome[i] > 'z' && nome[i] > 'Z')) return 1;
        i++;
    }

    return 0;
}

int verificar_email(char *email) {
    int tam = strlen(email);
    int arroba_pos = -1;
    int ponto_pos = -1;
    int i;

    // Verifica se há exatamente um "@" e pelo menos um "."
    for (i = 0; i < tam; i++) {
        if (email[i] == '@') {
            if (arroba_pos != -1) // Mais de um @
                return 1;
            arroba_pos = i;
        } else if (email[i] == '.') {
            ponto_pos = i;
        }
    }
    if (arroba_pos == -1 || ponto_pos == -1) // Falta @ ou .
        return 1;
    if (arroba_pos > ponto_pos) // . vem antes do @
        return 1;
    if (arroba_pos == 0 || ponto_pos == tam - 1) // . ou @ no início ou no final
        return 1;
    if (ponto_pos - arroba_pos == 1) // Nada entre o @ e o .
        return 1;

    return 0;
}

int verificar_bi(char *bi){
    int tamanho = 14;
    int digitos_iniciais = 7;
    int digito = 10;
    char caracter = '-';
    
    if(bi[8] != caracter || bi[10] != caracter || (int)strlen(bi) != tamanho) return 1;
    for(int i = 0; i<tamanho; i++){
        if((i <= digitos_iniciais) || (i == (digito - 1)) || (i == (tamanho - 1))){
            if((bi[i] - '0') > 9 || (bi[i] - '0') < 0) return 1;
        }
        if(i == 11 || i == 12){
            if(bi[i] < 'A' || bi[i] > 'Z') return 1;
        }
    }
    
    return 0;
}

int verificar_altura(float altura){
    if(altura < 0 || altura >250){
        printf("Altura inválida\n");
        return 1;
    }
    return 0;
}

int verificar_peso(float peso){
    if(peso < 0 || peso > 400){
        printf("Peso inválido\n");
        return 1;
    }
    return 0;
}

int verificar_tensao_minima(int tensao_m){
    if(tensao_m < (TENSAO_OTIMA_m - 20) || tensao_m > (HIPERTENSAO_III_MINIMA + 20)){
        printf("Tensão inválida\n");
        return 1;
    } 
    return 0;
}

int verificar_tensao_maxima(int tensao_M, int tensao_m){
    if(tensao_M < ~(TENSAO_OTIMA_M - 20) || tensao_M > (HIPERTENSAO_III_MAXIMA + 20)  || tensao_M < tensao_m){
        printf("Tensão inválida\n");
        return 1;
    } 
    return 0;
}