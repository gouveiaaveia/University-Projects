#include "node_struct.h"

RB_Node* create_RB_Node(long value) {
    RB_Node *newNode = (RB_Node*)malloc(sizeof(RB_Node));
    if (newNode == NULL) {
        printf("Error creating a new Node.\n");
        exit(0);
    }
    newNode->value = value;
    newNode->left = NULL;
    newNode->right = NULL;
    newNode->parent = NULL;
    newNode->color = 1; // Red
    return newNode;
}

void left_rotate(RB_Node **root, RB_Node *currentNode, int *rotationCount) {
    RB_Node *rightChild = currentNode->right;
    currentNode->right = rightChild->left;
    if (rightChild->left != NULL) rightChild->left->parent = currentNode;
    rightChild->parent = currentNode->parent;
    if (currentNode->parent == NULL) *root = rightChild;
    else if (currentNode == currentNode->parent->left) currentNode->parent->left = rightChild;
    else currentNode->parent->right = rightChild;
    rightChild->left = currentNode;
    currentNode->parent = rightChild;
    *rotationCount += 1;
}

void right_rotate(RB_Node **root, RB_Node *currentNode, int *rotationCount) {
    RB_Node *leftChild = currentNode->left;
    currentNode->left = leftChild->right;
    if (leftChild->right != NULL) leftChild->right->parent = currentNode;
    leftChild->parent = currentNode->parent;
    if (currentNode->parent == NULL) *root = leftChild;
    else if (currentNode == currentNode->parent->left) currentNode->parent->left = leftChild;
    else currentNode->parent->right = leftChild;
    leftChild->right = currentNode;
    currentNode->parent = leftChild;
    *rotationCount += 1;
}

void insert_fixup(RB_Node **root, RB_Node *currentNode, int *rotationCount) {
    while (currentNode->parent != NULL && currentNode->parent->color == 1) {
        if (currentNode->parent == currentNode->parent->parent->left) {
            RB_Node *uncleNode = currentNode->parent->parent->right;
            if (uncleNode != NULL && uncleNode->color == 1) {
                currentNode->parent->color = 0;
                uncleNode->color = 0;
                currentNode->parent->parent->color = 1;
                currentNode = currentNode->parent->parent;
            } else {
                if (currentNode == currentNode->parent->right) {
                    currentNode = currentNode->parent;
                    left_rotate(root, currentNode, rotationCount);
                }
                currentNode->parent->color = 0;
                currentNode->parent->parent->color = 1;
                right_rotate(root, currentNode->parent->parent, rotationCount);
            }
        } else {
            RB_Node *uncleNode = currentNode->parent->parent->left;
            if (uncleNode != NULL && uncleNode->color == 1) {
                currentNode->parent->color = 0;
                uncleNode->color = 0;
                currentNode->parent->parent->color = 1;
                currentNode = currentNode->parent->parent;
            } else {
                if (currentNode == currentNode->parent->left) {
                    currentNode = currentNode->parent;
                    right_rotate(root, currentNode, rotationCount);
                }
                currentNode->parent->color = 0;
                currentNode->parent->parent->color = 1;
                left_rotate(root, currentNode->parent->parent, rotationCount);
            }
        }
    }
    (*root)->color = 0;
}

void insert_RB(RB_Node **root, long value, int *rotationCount) {
    RB_Node *newNode = create_RB_Node(value);
    RB_Node *parentNode = NULL;
    RB_Node *currentNode = *root;
    while (currentNode != NULL) {
        parentNode = currentNode;
        if (newNode->value < currentNode->value) currentNode = currentNode->left;
        else if (newNode->value > currentNode->value) currentNode = currentNode->right;
        else {
            free(newNode);
            return;
        }
    }
    newNode->parent = parentNode;
    if (parentNode == NULL) *root = newNode;
    else if (newNode->value < parentNode->value) parentNode->left = newNode;
    else parentNode->right = newNode;
    newNode->left = NULL;
    newNode->right = NULL;
    newNode->color = 1;
    insert_fixup(root, newNode, rotationCount);
}

