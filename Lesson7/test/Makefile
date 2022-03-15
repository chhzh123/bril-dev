bc:
	clang -S -emit-llvm test.c -o test.ll

OPT_FLAGS = -enable-new-pm=0 -load ../build/skeleton/libSkeletonPass.so -skeleton
opt:
	opt $(OPT_FLAGS) < test.ll