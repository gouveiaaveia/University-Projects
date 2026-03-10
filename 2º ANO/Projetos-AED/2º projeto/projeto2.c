#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "node_struct.h"

#include "binary_tree.c"
#include "AVL_tree.c"
#include "RB_tree.c"
#include "TREAP_tree.c"

#define SIZE 100000

void freeTree(Node* root) {
    if (root == NULL) {
        return;
    }
    
    freeTree(root->left);
    freeTree(root->right);
    free(root);
}

void freeTreeAVL(AVL_Node* root) {
    if (root == NULL) {
        return;
    }
    
    freeTreeAVL(root->left);
    freeTreeAVL(root->right);
    free(root);
}

void freeTreeRB(RB_Node* root) {
    if (root == NULL) {
        return;
    }
    
    freeTreeRB(root->left);
    freeTreeRB(root->right);
    free(root);
}

void freeTreeTREAP(TREAP_Node* root) {
    if (root == NULL) {
        return;
    }
    
    freeTreeTREAP(root->left);
    freeTreeTREAP(root->right);
    free(root);
}

void printInOrder(Node *root) {
    if (root == NULL) {
        return;
    }

    // Visita recursivamente o filho esquerdo
    printInOrder(root->left);
    
    // Imprime o valor do nó atual
    printf("%d ", root->value);
    
    // Visita recursivamente o filho direito
    printInOrder(root->right);
}

int main() {

    srand(time(NULL));

    Node *root = NULL;
    AVL_Node *rootAVL = NULL;

    int rotations = 0;

    
    int *arr_A = malloc(SIZE * sizeof(int));
    int *arr_B = malloc(SIZE * sizeof(int));
    int *arr_C = malloc(SIZE * sizeof(int));
    int *arr_D = malloc(SIZE * sizeof(int));

    keys_A(arr_A);
    keys_B(arr_B);
    keys_C(arr_C);
    keys_D(arr_D);

    clock_t start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert(&root, arr_A[i]);
    }
    printf("(BINARY TREE TRANSVERSAL) TIME TO INSERT Keys_A: %lf seconds\n", (double)(clock() - start) / CLOCKS_PER_SEC);
    
    freeTree(root);
    root = NULL;
    
    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert(&root, arr_B[i]);
    }
    printf("(BINARY TREE TRANSVERSAL) TIME TO INSERT Keys_B: %lf seconds\n", (double)(clock() - start) / CLOCKS_PER_SEC);
    
    freeTree(root);
    root = NULL;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert(&root, arr_C[i]);
    }
    printf("(BINARY TREE TRANSVERSAL) TIME TO INSERT Keys_C: %lf seconds\n", (double)(clock() - start) / CLOCKS_PER_SEC);
    
    freeTree(root);
    root = NULL;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert(&root, arr_D[i]);
    }
    printf("(BINARY TREE TRANSVERSAL) TIME TO INSERT Keys_D: %lf seconds\n", (double)(clock() - start) / CLOCKS_PER_SEC);

    freeTree(root);
    printf("\n");

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootAVL = insert_AVL(rootAVL, arr_A[i], &rotations);
    }
    printf("(AVL TREE) TIME TO INSERT Array_A: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeAVL(rootAVL);

    rootAVL = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootAVL = insert_AVL(rootAVL, arr_B[i], &rotations);
    }
    printf("(AVL TREE) TIME TO INSERT Array_B: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeAVL(rootAVL);

    rootAVL = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootAVL = insert_AVL(rootAVL, arr_C[i], &rotations);
    }
    printf("(AVL TREE) TIME TO INSERT Array_C: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeAVL(rootAVL);

    rootAVL = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootAVL = insert_AVL(rootAVL, arr_D[i], &rotations);
    }
    printf("(AVL TREE) TIME TO INSERT Array_D: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeAVL(rootAVL);
    printf("\n");

    RB_Node *rootRB = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert_RB(&rootRB, arr_A[i], &rotations);
    }
    printf("(RED-BLACK TREE) TIME TO INSERT Array_A: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeRB(rootRB);
    rootRB = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert_RB(&rootRB, arr_B[i], &rotations);
    }
    printf("(RED-BLACK TREE) TIME TO INSERT Array_B: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);


    freeTreeRB(rootRB);
    rootRB = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert_RB(&rootRB, arr_C[i], &rotations);
    }
    printf("(RED-BLACK TREE) TIME TO INSERT Array_C: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeRB(rootRB);
    rootRB = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        insert_RB(&rootRB, arr_D[i], &rotations);
    }
    printf("(RED-BLACK TREE) TIME TO INSERT Array_D: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeRB(rootRB);
    printf("\n");

    TREAP_Node *rootTREAP = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootTREAP = insert_TREAP(rootTREAP, arr_A[i], &rotations);
    }
    printf("(TREAP TREE) TIME TO INSERT Array_A: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeTREAP(rootTREAP);
    rootTREAP = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootTREAP = insert_TREAP(rootTREAP, arr_B[i], &rotations);
    }
    printf("(TREAP TREE) TIME TO INSERT Array_B: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeTREAP(rootTREAP);
    rootTREAP = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootTREAP = insert_TREAP(rootTREAP, arr_C[i], &rotations);
    }
    printf("(TREAP TREE) TIME TO INSERT Array_C: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeTREAP(rootTREAP);
    rootTREAP = NULL;
    rotations = 0;

    start = clock();
    for(int i = 0; i < SIZE; i++) {
        rootTREAP = insert_TREAP(rootTREAP, arr_D[i], &rotations);
    }
    printf("(TREAP TREE) TIME TO INSERT Array_D: %lf seconds with %d rotations\n", (double)(clock() - start) / CLOCKS_PER_SEC, rotations);

    freeTreeTREAP(rootTREAP);
    
    free(arr_A);
    free(arr_B);
    free(arr_C);
    free(arr_D);

    return 0;
}