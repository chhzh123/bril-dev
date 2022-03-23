# Lesson 8 - Loop Optimization

* First, pick Bril or LLVM as your starting point.
    * You can work in the SSA form of Bril if you want.
    * If you pick Bril, you’ll need to find the natural loops yourself. If you pick LLVM, you can use a LoopPass to skip that step, but of course other parts of the implementation will be trickier.
* Then, pick your optimization. You can either:
    * Choose one of the loop-based optimizations mentioned above in this lesson. (Including one of the ones I just mentioned at the end without describing in detail.) (If you’re having trouble deciding, I recommend LICM.)
    * Propose your own. (DM me on Zulip before you start working on it to clear your idea.)
* Implement your optimization.
    * Rigorously evaluate its performance impact. See the SIGPLAN empirical evaluation guidelines for the definition of “rigorous.”
    * In Bril, you can use the Bril benchmarks.
    * If you choose LLVM, select an existing (small!) benchmark suite such as Embench. Please violate the SIGPLAN guideline about using complete benchmark suites, an cherry-pick a convenient subset, to make this evaluation tractable.

Please follow the instructions below to run the program. The basic skeleton program comes from the course [repository](https://github.com/sampsyo/llvm-pass-skeleton).
```bash
mkdir build
cd build
cmake ..
make

cd ../test
make opt
```

In this task, I implemented the loop reordering/interchanging pass in LLVM. My code can be found [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson8/skeleton/LoopAnalysis.cpp). I reused some facilities from my loop analysis pass in [Lesson 7](https://github.com/chhzh123/bril-dev/blob/master/Lesson7), and again compiled and run the program using [**LLVM 14**](https://github.com/llvm/llvm-project/releases/tag/llvmorg-14.0.0-rc1) with the new [pass manager](https://blog.llvm.org/posts/2021-03-26-the-new-pass-manager/).


<!-- https://llvm.org/doxygen/LoopInterchange_8cpp_source.html -->

## Implementation
At first I thought it should be easy to interchange two loops just like cutting and pasting the for-loop header in an IDE, but later I found it was very troublesome in LLVM IR. Since a loop is orgainized as several basic blocks as shown in the following figure (source from [LLVM Tutorial](https://llvm.org/docs/LoopTerminology.html#id7)), we need to carefully move those blocks and change their inter-relationship.

![](https://llvm.org/docs/_images/loop-terminology.svg)

The inputs of my reordering pass are two loops (outer loop and inner loop). I firstly extract all the loop preheaders, headers, latches, and exits from the loops, and then use `moveBefore` to move those basic blocks to corresponding places. Notice there is no `swap` function in LLVM, so I need to record the successors and predecessors of the original basic blocks, and do at least two movements for each pair of inner and outer loop blocks. After that, all the related branch instructions should be updated and points to the new basic blocks.

There is one more tricky thing here. If the loop to be reordered is the top-level loop, its preheader may be the entry block of the function. In this case, we need to separate the block and create a new preheader block for that loop. Also, the exit block may also connect with the following blocks, so it needs to be separated as well.

For programming interface, I allow users to specify which loops to be interchanged and can do mulitple interchanges in one pass.

## Evaluation
As a golden test example, I tested the three-nested-loop GEMM on my machine, and consider 6 possible loop permutations to see the performance of different traversal orders. I set the matrix size to be 1024x1024, and my CPU is Intel Xeon Silver 4214 with 16.5MB L3 cache.
```cpp
for (int i = 0; i < SIZE; ++i)
    for (int j = 0; j < SIZE; ++j)
        for (int k = 0; k < SIZE; ++k)
            C[i][j] += A[i][k] * B[k][j];
```

The results are shown below, and the speedup are normalized by the time of the original `ijk` order.
| Order | Time (us) | Speedup |
| :-------: | :---: | :---: |
| ijk | 5365352 | 1x |
| ikj | 3041839 | 1.76x |
| jik | 5495723 | 0.97x |
| jki | 11241154 | 0.48x |
| kij | 3070182 | 1.75x | 
| kji | 10926492 | 0.49x |

We can obtain the following speedup comparison. The conclusion is the same as tue GEMM example (Fig 6.46) in the famous introductory book [CSAPP](https://csapp.cs.cmu.edu/).
If the traversal order is the same as the data organization (`ikj`), there will be a large speedup due to the improved cache locality. This indirectly proves the correctness of my pass and shows the loop interchanging can indeed improve the performance of the program.
```
kij \~ ikj < ijk \~ jik < kji \~ jki
```