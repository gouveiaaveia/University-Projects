#include "node_struct.h"


// por largura - por camadas (fila)
// por profundidade - pre-ordem, in-ordem, pos-ordem (pilha)

Node *createNode(long value) {
    Node *newNode = malloc(sizeof(Node));
    if (newNode == NULL) {
        fprintf(stderr, "Erro na alocação de memória para o nó.\n");
        exit(EXIT_FAILURE);
    }
    newNode->value = value;
    newNode->left = NULL;
    newNode->right = NULL;
    return newNode;
    
}

/*
void insert(Node** root, long value) {
    queue *q = create();
    Node *newNode = createNode(value);

    if(*root == NULL) {
        *root = newNode;
        return;
    }

    insert_q(q, *root);
    Node *temp;

    while(!empty(q)) {
        temp = pop(q);

        if(temp->value == value) {
            free(newNode);
            delete_q(q);
            return;
        }

        if(temp->left == NULL) {
            temp->left = newNode;
            return;
        } else {
            insert_q(q, temp->left);
        }

        if(temp->right == NULL) {
            temp->right = newNode;
            return;
        } else {
            insert_q(q, temp->right);
        }
    }
    delete_q(q);
}

*/


void insert(Node** root, long value) {
    Node *newNode = createNode(value);

    if (*root == NULL) {
        *root = newNode;
        return;
    }

    Node *currentNode;
    Node *nodeQueue[SIZE];
    long queueFront = -1, queueRear = -1;

    nodeQueue[++queueRear] = *root;

    while (queueFront != queueRear) {
        currentNode = nodeQueue[++queueFront];

        if (currentNode->value == value) {
            free(newNode);
            return;
        }

        if (currentNode->left == NULL) {
            currentNode->left = newNode;
            return;
        } else {
            nodeQueue[++queueRear] = currentNode->left;
        }

        if (currentNode->right == NULL) {
            currentNode->right = newNode;
            return;
        } else {
            nodeQueue[++queueRear] = currentNode->right;
        }
    }
}