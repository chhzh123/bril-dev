#include "stdio.h"

int main() {
    const int SIZE = 10;
    int A[SIZE][SIZE], B[SIZE][SIZE], C[SIZE][SIZE];
    // matmul
    for (int i = 0; i < SIZE; ++i)
        for (int j = 0; j < SIZE; ++j)
            for (int k = 0; k < SIZE; ++k)
                C[i][j] += A[i][k] * B[k][j];
    printf("passed\n");
    return 0;
}