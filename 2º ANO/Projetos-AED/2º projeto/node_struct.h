#ifndef NODE_STRUCT_H
#define NODE_STRUCT_H

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "keys.c"

// Struct for the Binary Tree
typedef struct Node{
    int value;
    struct Node *left;
    struct Node *right;
}Node;

// Struct for the AVL Tree
typedef struct AVL_Node{
    long value;
    struct AVL_Node *left;
    struct AVL_Node *right;
    int height;
} AVL_Node;

// Struct for Red Black Tree
typedef struct RB_Node{
    long value;
    struct RB_Node *left;
    struct RB_Node *right;
    struct RB_Node *parent;
    int color; // 0 for black, 1 for red
}RB_Node;


typedef struct TREAP_Node{
    long value;
    long priority;
    struct TREAP_Node *left;
    struct TREAP_Node *right;
}TREAP_Node;

/* Struct for the Queue

typedef struct q_node {
    Node *node;
    struct q_node *next;
}q_node;

typedef struct {
    q_node *start;
    q_node *end;
}queue;

queue *create() {
    queue *q = malloc(sizeof(queue));
    if (q == NULL) {
        fprintf(stderr, "Erro na alocação de memória para a fila.\n");
        exit(EXIT_FAILURE);
    }
    q->start = NULL;
    q->end = NULL;
    return q;
}


int empty(queue *q){
    if (q->start == NULL) return 1;
    else return 0;
}

void delete_q(queue *q){
    q_node *temp_ptr;
    while(!empty(q)){
        temp_ptr = q->start;
        q->start = q->start->next;
        free(temp_ptr);
    }
    q->end =NULL;
}

void insert_q(queue *q, Node *node){
    q_node * temp_ptr;
    temp_ptr = (q_node *) malloc (sizeof(q_node));
    if (temp_ptr != NULL){
        temp_ptr->node = node;
        temp_ptr->next = NULL;
        if(empty(q)) q->start = temp_ptr;
        else q->end->next = temp_ptr;
        q->end = temp_ptr;
    }
}

Node *pop(queue * q){
    q_node *temp_ptr;
    Node *node;
    if(!empty(q)){
        temp_ptr = q->start;
        node = temp_ptr->node;
        q->start = q->start->next;
        if(empty(q)) q->end = NULL;
        free(temp_ptr);
        return node;
    }
    return 0;
}

*/

#endif