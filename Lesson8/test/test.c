#include "stdio.h"
#include "sys/time.h"

#define SIZE 2048

int A[SIZE][SIZE], B[SIZE][SIZE], C[SIZE][SIZE];

int main() {
  // matmul
  struct timeval stop, start;
  gettimeofday(&start, NULL);
  for (int i = 0; i < SIZE; ++i)
    for (int j = 0; j < SIZE; ++j)
      for (int k = 0; k < SIZE; ++k)
        C[i][j] += A[i][k] * B[k][j];
  gettimeofday(&stop, NULL);
  printf("took %lu us\n", (stop.tv_sec - start.tv_sec) * 1000000 + stop.tv_usec - start.tv_usec); 
  printf("passed\n");
  return 0;
}