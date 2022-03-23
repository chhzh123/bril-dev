all:
	clang -Xclang -load -Xclang ../build/skeleton/libSkeletonPass.so test.c -o test

test.ll: test.c
	clang -S -emit-llvm test.c -o test.ll

test2.ll: test.c
	clang -S -emit-llvm test.c -o test2.ll

OPT_FLAGS = -enable-new-pm=0 -load ../build/skeleton/libSkeletonPass.so -loop-analysis
test.opt.ll: test.ll
	opt $(OPT_FLAGS) < test.ll > test.opt.ll