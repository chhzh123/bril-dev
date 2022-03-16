# Lesson 7 - LLVM

<!-- Follow the LLVM tutorial blog post far enough to implement a pass that changes program execution.
This is intentionally open-ended. You can be as ambitious or as unambitious as you want.
An example of an unambitious but acceptable task would be to print out a message every time the program uses floating-point division.
An example of an ambitious task would be to implement a fancy optimization on LLVM IR and make sure it speeds things up in actual wall-clock time execution.
Find a real-ish C/C++ program somewhere and run your pass on it to observe the results. -->

Please follow the instructions below to run the program. The basic skeleton program comes from the course [repository](https://github.com/sampsyo/llvm-pass-skeleton).
```bash
mkdir build
cd build
cmake ..

cd ../test
make opt
```

<!-- Ref:
https://www.cs.cornell.edu/courses/cs6120/2022sp/lesson/8/
-->

In this task, I implemented a **memory access analysis** pass for nested loops. I compiled and run my pass using the latest [**LLVM 14**](https://github.com/llvm/llvm-project/releases/tag/llvmorg-14.0.0-rc1) branch with the new [pass manager](https://blog.llvm.org/posts/2021-03-26-the-new-pass-manager/). My code can be found [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson7/skeleton/LoopAnalysis.cpp).


## Background
When C/C++ programs are lowered to LLVM IR, they lose high-level information of loops and memory accesses. The loops are translated into several basic blocks (preheader, body, latch, etc.). Memory access like `A[i+1]` may be translated into several lines of code below, which loses original index representation and poses challenges on implementing memory-related optimization using techniques like [polyhedral analysis](https://en.wikipedia.org/wiki/Polytope_model). Thus, in order to better analyze the memory dependency and optimize the access patterns in a loop nest, we need to first extract the load/store instructions with correct indices. In this task, I inspected LLVM IR and output the original array and indices. Since this is the preparation for the task in Lesson 8, it is not that fancy but just simple arithmetic expression propagation in the LLVM framework.

```llvm
  %12 = load i32, i32* %i, align 4
  %add13 = add nsw i32 %12, 1
  %idxprom14 = sext i32 %add13 to i64
  %arrayidx15 = getelementptr inbounds [10 x i32], [10 x i32]* %A, i64 0, i64 %idxprom14
  %13 = load i32, i32* %arrayidx15, align 4
```


## Implementation
To find the loops in LLVM IR, I reuse the `LoopInfoWrapperPass`. For each loop, I traverse the basic block and instructions inside it. I first find the [`getelementptr`](https://blog.yossarian.net/2020/09/19/LLVMs-getelementptr-by-example) instruction, which is hard to understand the parameters in the first place, but actually its operands are just depicting the data types and the pointers to some specific positions in an array. For each `getelementptr`, I get its users. If the user is a load/store instruction, I traverse back from the `%idx` to get the complete expression of the index.

I created an instruction visitor class `InstVisitor` and implemented a dispatching method `visit` to traverse back from the final expression based on different arithmetic instructions, which is essentially doing an inorder tree traversal.


## Test
To run my pass for real programs, I first use `clang` to generate bytecode (`*.ll`) and use `opt` to load the library. Moreover, `-enable-new-pm=0` should be set for the new pass manager.

The following test program shows several different memory access patterns. Currently, I only consider 1D arrays, so high-dimensional arrays should be firstly flattened into 1D.

```cpp
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
```

The output of my pass is shown below.

```cpp
Loop 0:
Load:   %28 = load i32, i32* %arrayidx52, align 4
Original: A[i37*3+k45]
Load:   %31 = load i32, i32* %arrayidx56, align 4
Original: B[k45*3+j41]
Store:   store i32 %mul57, i32* %arrayidx61, align 4
Original: C[i37*3+j41]

Loop 1:
Load:   %18 = load i32, i32* %arrayidx27, align 4
Original: A[k*3+1]
Load:   %20 = load i32, i32* %arrayidx29, align 4
Original: B[k/2]
Store:   store i32 %add30, i32* %arrayidx33, align 4
Original: C[k*2]

Loop 2:
Load:   %9 = load i32, i32* %arrayidx9, align 4
Original: A[j-1]
Load:   %11 = load i32, i32* %arrayidx11, align 4
Original: A[j]
Load:   %13 = load i32, i32* %arrayidx15, align 4
Original: A[j+1]
Store:   store i32 %add16, i32* %arrayidx18, align 4
Original: B[j]

Loop 3:
Load:   %2 = load i32, i32* %arrayidx, align 4
Original: A[i]
Load:   %4 = load i32, i32* %arrayidx2, align 4
Original: B[i]
Store:   store i32 %add, i32* %arrayidx4, align 4
Original: C[i]
```

We can see my pass exactly captures the four loops in the program (in a reversed order), and recovers the original arrays and indices for load/store instructions, even for complex indices or multi-dimensional nested loops. Notice some of the variables are renamed by LLVM, so there exist variable names like `i37` or `k45` in the result, but this does not affect the correctness.


## Discussions
Though I finally made my pass work, I still have to say, the documentation of LLVM is reeeeally terrible. In the very beginning, I thought the [tutorial](https://llvm.org/docs/WritingAnLLVMPass.html) page should reflect the latest changes. However, it didn't, and was even somehow misleading. After searching on Google, I could only find how to get the new pass manager to work on a [discussion thread](https://groups.google.com/g/llvm-dev/c/kQYV9dCAfSg)! Moreover, even the doxygen provides the class method signature, it is still hard to understand what the methods are used for and how to use them. Actually I found pulling the whole llvm-project and directly searching some methods offline may be more helpful. Looking at real code snippets with contexts before and behind function calls is much easier to understand than directly looking at the documentation.

Since I've been working on a [MLIR](https://mlir.llvm.org/) project for several months, I can see lots of similarities between MLIR and LLVM, including how they traverse the function body and how the facilities look like. But I think the biggest difference between them may be the abstraction level. While LLVM IR is low-level and closed to real machines, many MLIR dialects are high-level and provide more facilities to operate on loops and memory accesses. At first, I wanted to do some real loop optimizations based on LLVM, but I found it was hard to print out readable code of loops and I could not easily convert the IR back to C/C++. However, with the affine/scf dialect in MLIR, we can dump the for loops in a human-readable C-like way, and it is also more intuitive to view and access the loops when doing optimizations like interchanging or fusing. After some programming practice in LLVM and MLIR, I kind of understand the rationale behind several layers of IR abstraction in nowadays deep learning compilers. Some machine-dependent optimizations are easier to express in a low-level abstraction, while loop or memory optimizations are easier to be implemented with a high-level IR, so progressive lowering is helpful to realize the optimizations in a suitable abstraction and gradually add hardware details to the program.