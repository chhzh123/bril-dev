bc: test.c
	clang -S -emit-llvm test.c -o test.ll

# OPT_FLAGS = -enable-new-pm=0 -load ../build/skeleton/libSkeletonPass.so -skeleton
OPT_FLAGS = -enable-new-pm=0 -load ../build/skeleton/libSkeletonPass.so -loop-analysis
opt: test.ll
	opt $(OPT_FLAGS) < test.ll