#include "node_struct.h"

TREAP_Node* create_TREAP_Node(long value){
    TREAP_Node *newNode = (TREAP_Node*) malloc(sizeof(TREAP_Node));

    if(newNode == NULL){
        printf("Error creating a new Node.\n");
        exit(0);
    }

    newNode->value = value;
    newNode->priority = rand() % (SIZE * 10) + 1;
    newNode->left = NULL;
    newNode->right = NULL;

    return newNode;
}

TREAP_Node* rightRotate_TREAP(TREAP_Node *root, int* rotations){
    TREAP_Node *newRoot = root->left;
    TREAP_Node *temp = newRoot->right;

    newRoot->right = root;
    root->left = temp;

    *rotations += 1;

    return newRoot;
}


TREAP_Node* leftRotate_TREAP(TREAP_Node *root, int* rotations){
    TREAP_Node *newRoot = root->right;
    TREAP_Node *temp = newRoot->left;

    newRoot->left = root;
    root->right = temp;

    *rotations += 1;

    return newRoot;
}

TREAP_Node* insert_TREAP(TREAP_Node *root, long value, int* rotations){
    if(root == NULL){
        return create_TREAP_Node(value);
    }

    if(value < root->value){
        root->left = insert_TREAP(root->left, value, rotations);
        
        if(root->left->priority > root->priority){
            root = rightRotate_TREAP(root, rotations);
        }
    }else if(value > root->value){
        root->right = insert_TREAP(root->right, value, rotations);

        if(root->right->priority > root->priority){
            root = leftRotate_TREAP(root, rotations);
        }
    }else{
        return root;
    }

    return root;
}