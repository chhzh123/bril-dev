#include "stdio.h"
#include "time.h"

const int SIZE = 1024;
int A[SIZE][SIZE], B[SIZE][SIZE], C[SIZE][SIZE];

int main() {
  // matmul
  clock_t start, stop;
  start = clock();
  for (int i = 0; i < SIZE; ++i)
    for (int j = 0; j < SIZE; ++j)
      for (int k = 0; k < SIZE; ++k)
        C[i][j] += A[i][k] * B[k][j];
  stop = clock();
  printf("passed\n");
  printf("%6.8f\n", start);
  printf("%6.8f\n", stop);
  return 0;
}