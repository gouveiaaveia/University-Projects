#ifndef MAIN_H
#define MAIN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <unistd.h>

#define MAX 100

// Constantes para classificação da tensão arterial
#define TENSAO_OTIMA_M 120
#define TENSAO_OTIMA_m 80
#define TENSAO_NORMAL_MAXIMA_m 120
#define TENSAO_NORMAL_MAXIMA_M 129
#define TENSAO_NORMAL_MINIMA_m 80
#define TENSAO_NORMAL_MINIMA_M 84
#define TENSAO_NORMAL_ALTA_MAXIMA_M 130
#define TENSAO_NORMAL_ALTA_MAXIMA_m 139
#define TENSAO_NORMAL_ALTA_MINIMA_M 85
#define TENSAO_NORMAL_ALTA_MINIMA_m 89
#define HIPERTENSAO_I_MAXIMA_m 140
#define HIPERTENSAO_I_MAXIMA_M 159
#define HIPERTENSAO_I_MINIMA_m 90
#define HIPERTENSAO_I_MINIMA_M 99
#define HIPERTENSAO_II_MAXIMA_m 160
#define HIPERTENSAO_II_MAXIMA_M 179
#define HIPERTENSAO_II_MINIMA_m 100
#define HIPERTENSAO_II_MINIMA_M 109
#define HIPERTENSAO_III_MAXIMA 180
#define HIPERTENSAO_III_MINIMA 110
#define HIPERTENSAO_SISTOLICA_ISOLADA_MAXIMA 140 
#define HIPERTENSAO_SISTOLICA_ISOLADA_MINIMA 90 

typedef struct {
    int ID;
    int dia, mes, ano;
    char nome[MAX];
    char cartao_cidadao[MAX];
    int telefone;
    char email[MAX];
} Registo;

typedef struct {
    int id;
    int dia, mes, ano;
    int tensao_minima;
    int tensao_maxima;
    char avaliacao_tesao[MAX];
    float altura;
    float peso;
} Info;

typedef struct noListaRegisto {
    Info info;
    struct noListaRegisto *prox;
} *pListaRegisto;

typedef struct noLista {
    Registo pessoa_info;
    pListaRegisto lista_registo;
    struct noLista *prox;
} *pLista;

typedef struct noListaTensao {
    pLista tensao_alta;
    struct noListaTensao *prox;
} *pListaTensao;

// Protótipos das funções para manipulação da lista de pacientes
pLista cria();
int vazia(pLista);
pLista destroi(pLista);
void procura(pLista, char *, pLista *, pLista *);
void insere(pLista, Registo, pListaRegisto);
pLista pesquisa(pLista, int);
void imprime(pLista, int *);

// Protótipos das funções para manipulação da lista de registos
pListaRegisto cria_registo();
int vazia_registo(pListaRegisto);
pListaRegisto destroi_registo(pListaRegisto);
void procura_registo(pListaRegisto, int , pListaRegisto *, pListaRegisto *);
void insere_registo(pListaRegisto, Info);
pListaRegisto pesquisa_registo(pListaRegisto, int);
void imprime_registo(pListaRegisto);

// Protótipos das funções para manipulação da lista de pacientes com tensão alta
pListaTensao cria_tensao();
int vazia_tensao(pListaTensao);
pListaTensao destroi_tensao(pListaTensao);
void procura_tensao(pListaTensao, pLista *, pListaTensao *, pListaTensao *);
void insere_tensao(pListaTensao, pLista );
void imprime_tensao(pListaTensao);

// Protótipos das funções relacionadas ao menu e interação com o usuário
void menu(pLista *, int *);
void mais_informacao(pLista *, int *);
void pedir_informacao_registo(pLista *, int *);
void registo(pLista *, Registo);
void pedir_medicoes(pLista *, int, int *);
void registo_medicoes(pLista *, pListaRegisto, int);
void mostrar_informacao(pLista, int, int *);
void remover_paciente(pLista *, int *);
int pedir_id();
void voltar();
void avaliar_tensao(char *, int *, int *);
void pacientes_tensao_alta(pLista , int *);
void tensao_maxima(pLista , int *);


//Verificações de informação
int verificar_data(int, int, int);
int verifica_data_consula_nascimento(pLista, pListaRegisto);
int verificar_email(char *);
int verificar_nome(char *);
int verificar_bi(char *);
int verificar_altura(float);
int verificar_peso(float);
int verificar_tensao_minima(int);
int verificar_tensao_maxima(int, int);

//Funções ficheiros
void criar_ficheiro_doentes(pLista *);
void criar_ficheiro_registos(pLista *);
int carregar_pacientes_do_ficheiro(pLista *, int *);
void carregar_registos_pacientes_ficheiro(pLista *);

#endif
