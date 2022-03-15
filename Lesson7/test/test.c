#include "stdio.h"

int main() {
    int A[10], B[10], C[10];
    for (int i = 0; i < 9; ++i) {
        C[i] = A[i+1] + B[i+1];
    }
    return 0;
}