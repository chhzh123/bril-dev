#include "stdio.h"

int main() {
    int A[1024][1024], B[1024][1024], C[1024][1024];
    // 2D: matmul
    for (int i = 0; i < 1024; ++i)
        for (int j = 0; j < 1024; ++j)
            for (int k = 0; k < 1024; ++k)
                C[i][j] += A[i][k] * B[k][j];
    return 0;
}