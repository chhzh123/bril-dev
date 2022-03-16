#include "stdio.h"

int main() {
    int A[10], B[10], C[10];
    // simple
    for (int i = 0; i < 10; ++i) {
        C[i] = A[i] + B[i];
    }
    // 1D stencil
    for (int j = 1; j < 9; ++j) {
        B[j] = A[j - 1] + A[j] + A[j + 1];
    }
    // complex indices
    for (int k = 1; k < 3; ++k) {
        C[k * 2] = A[k * 3 + 1] + B[k / 2];
    }
    // 2D: matmul
    for (int i = 0; i < 3; ++i)
        for (int j = 0; j < 3; ++j)
            for (int k = 0; k < 3; ++k)
                C[i * 3 + j] = A[i * 3 + k] * B[k * 3 + j];
    return 0;
}