#include "node_struct.h"

AVL_Node* createNodeAVL(long value) {
    AVL_Node *newNode = (AVL_Node*) malloc(sizeof(AVL_Node));

    if(newNode == NULL) {
        printf("Error creating a new Node.\n");
        exit(0);
    }

    newNode->value = value;
    newNode->left = NULL;
    newNode->right = NULL;
    newNode->height = 1;

    return newNode;
}

int max(int a, int b) { return (a > b) ? a : b; }

int getHeight(AVL_Node *root){
    if(root == NULL){
        return 0;
    }
    return root->height;
}

int getBalance(AVL_Node *root){
    if(root == NULL){
        return 0;
    }
    return getHeight(root->left) - getHeight(root->right);
}

AVL_Node* rightRotate(AVL_Node *root, int *rotations){
    AVL_Node *newRoot = root->left;
    AVL_Node *temp = newRoot->right;

    newRoot->right = root;
    root->left = temp;

    root->height = 1 + max(getHeight(root->left), getHeight(root->right));
    newRoot->height = 1 + max(getHeight(newRoot->left), getHeight(newRoot->right));

    *rotations += 1;

    return newRoot;
}

AVL_Node* leftRotate(AVL_Node *root, int *rotations){
    AVL_Node *newRoot = root->right;
    AVL_Node *temp = newRoot->left;

    newRoot->left = root;
    root->right = temp;

    root->height = 1 + max(getHeight(root->left), getHeight(root->right));
    newRoot->height = 1 + max(getHeight(newRoot->left), getHeight(newRoot->right));

    *rotations += 1;

    return newRoot;
}


AVL_Node* insert_AVL(AVL_Node* root, long value, int *rotations){

    if(root == NULL) {
        return createNodeAVL(value);
    }

    if(value < root->value){
        root->left = insert_AVL(root->left, value, rotations);
    }else if (value > root->value){
        root->right = insert_AVL(root->right, value, rotations);
    }else{
        return root;
    }

    root->height = 1 + max(getHeight(root->left), getHeight(root->right));

    int balance = getBalance(root);

    if(balance > 1 && value < root->left->value){
        return rightRotate(root, rotations);
    }

    if(balance < -1 && value > root->right->value){
        return leftRotate(root, rotations);
    }

    if(balance > 1 && value > root->left->value){
        root->left = leftRotate(root->left, rotations);
        return rightRotate(root, rotations);
    }

    if(balance < -1 && value < root->right->value){
        root->right = rightRotate(root->right, rotations);
        return leftRotate(root, rotations);
    }

    return root;
}
