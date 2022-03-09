# Lesson 6 - SSA

<!--
* Implement the “into SSA” and “out of SSA” transformations on Bril functions.
** One thing to watch out for: a tricky part of the translation from the pseudocode to the real world is dealing with variables that are undefined along some paths.
** Previous 6120 adventurers have found that it can be surprisingly difficult to get this right. Leave yourself plenty of time, and test thoroughly.
* As usual, convince yourself that your implementation actually works!
** You will want to make sure the output of your “to SSA” pass is actually in SSA form. There’s a really simple is_ssa.py script that can check that for you.
** You’ll also want to make sure that programs do the same thing when converted to SSA form and back again. Fortunately, brili supports the phi instruction, so you can interpret your SSA-form programs if you want to check the midpoint of that round trip.
* For bonus “points,” implement global value numbering for SSA-form Bril code.
-->

Please follow the instructions below to run the program.
```bash
# to ssa
bril2json < test/ssa/loop-ssa.bril | python3 to_ssa.py | bril2txt
# from ssa
bril2json < test/ssa_roundtrip/argwrite.bril | python3 to_ssa.py | python3 from_ssa.py | brili 3
# gvn
bril2json < test/gvn/branch.bril | python gvn.py | bril2txt

# test
make test
```

<!-- https://groups.seas.harvard.edu/courses/cs153/2018fa/lectures/Lec23-SSA.pdf
https://www.cs.princeton.edu/courses/archive/spr04/cos598C/lectures/11-SSA-3x1.pdf
https://www.ics.uci.edu/~yeouln/course/ssa.pdf
-->

In this assignment, I implemented the "into SSA" and "out of SSA" transformations, and tested them using `turnt`. Also, I followed the algorithm in [Value Numbering](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.36.8877&rep=rep1&type=pdf) to implement **GVN**. Code can be found in my [repository](https://github.com/chhzh123/bril-dev/tree/master/Lesson6). All the "from_ssa", "to_ssa", "ssa_roundtrip", and "gvn" tests are passed.

## Converting to SSA
There are two steps in the SSA algorithm, the first one is phi-node insertion, and the second one is variable renaming. The pseudocode is very concise and misses lots of details. I was also confused about the phi-node part of the insertion algorithm in the first place and was misled that we insert an argument to the phi-node when we traverse the dominance frontier of `def`. Considering the following code that can bypass `x` from the `.entry` block to the `.end` block, we may probably get the phi-node with only one argument from `.left` since `.end` only in `.left`'s dominance frontier but not in `.entry`'s (which is an empty set).
```
@main(cond: bool) {
.entry:
  x: int = const 0;
  br cond .left .end;
.left:
  x: int = const 1;
  jmp .end;
.end:
  print x;
}
```

Later then I found that was incorrect. "Add a phi-node to block" means directly adding `v = phi v v .b1 .b2` to block, and those `v` are just placeholders that will be given real names in the next pass. And how many predecessors the block has, how many arguments the phi node will have. The values that are not defined in some branches will be marked as `undefined` also in the next pass.

Also, "add a phi-node to block unless we have done so already" implies the phi-node is of variable `v`. A block can actually have multiple phi-nodes of different variables, so we need to exactly test if the phi-node of `v` exists, otherwise we do not insert it.

The renaming part is also tricky with several details that need to be paid attention to. For replacing the argument names, I added a constraint of not modifying the phi-node arguments. Since some of the phi-node arguments have already been written by the predecessor blocks, it will be overwritten if we do not distinguish the phi-node from other operations.

The phi-node renaming is probably the most confusing part -- "assuming p is for a variable v, make it read from stack[v]" -- the pseudocode does not tell us which phi-node argument we should modify and how to do that. I finally found some clues from this [lecture note](https://www.ics.uci.edu/~yeouln/course/ssa.pdf) -- "replace the `j`-th operand of `RHS(p)` by `Top(Stacks[v])`", where "`j` is the position in `s`’s phi-function corresponding to block b". So we know we can replace the `j`-th operand of the phi-node by the top of the stack. If the stack is empty, then it means the value comes from a branch that has no definitions of that variable, so that operand should be set as `__undefined`.

Lastly, I added some enhancements to my SSA algorithm in order to pass *all* the test cases:
* Add my entry block at the beginning of the program (`while.bril`). This is always useful, especially for the program whose entry block is the header of a loop (which has a backedge). If the entry block is empty without doing any computation, I will eliminate it in the end.
* Support function arguments (`argwrite.bril`). This only needs to add those arguments into the variable stack at initialization.
* Support multiple functions (`loop-branch.bril`). Traverse all the functions and run the SSA algorithm for each of them.
* Type specification (`loop.bril`). The pseudocode does not mention anything about variable types, but to generate correct phi-nodes, we need to preserve the type information. This can be done by simply adding types into the variable definition map.
* Support phi node in the original program (`if-ssa.bril`). I rename the original `phi` node to `phi_` so that it can be viewed as normal operations whose arguments will be replaced by the top name of the stack. Finally, the `phi_` operation will be changed back to `phi` in order to be parsed by `brili`.


## Converting from SSA
This is much easier than converting a program from non-SSA form to SSA form. As the [algorithm](https://www.cs.cornell.edu/courses/cs6120/2022sp/lesson/6/) describes, we only need to add `id` operations in the predecessor blocks of the block with phi-node, and then remove the phi instruction. There is one little thing to mention, the `id` instruction should be inserted before `jmp`/`br`, otherwise the variable may become undefined since the code may be executed before it jumps to different blocks.


## Global Value Numbering
I also followed the [Value Numbering](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.36.8877&rep=rep1&type=pdf) paper written by KEITH D. COOPER and L. TAYLOR SIMPSON in 1995 to implement global value numbering, which is the dominator-based value numbering technique (DVNT) in Figure 4. The pseudocode is very clear. Since we have implemented [LVN](https://github.com/chhzh123/bril-dev/blob/master/Lesson3/lvn.py) in Lesson3, the basic data structure of GVN is quite similar to that one. I used `(op, VN[arg[0]], VN[arg[1]], ...)` as the key of the GVN table and the canonical variable names (i.e. the SSA values) as the value of the table. After transforming the program to SSA form, we do not have duplicated assignments to the same variable, thus the SSA name can be directly used as the canonical name which also simplifies the algorithm.

For the part of "adjust the phi-function inputs in s", it is similar to what I did in SSA conversion. We need to first find out the corresponding argument index that refers to the current block, and change that argument to the canonical name.

I took the example in the paper (Fig. 5) to test the correctness of my implementation.

```
@main(a0: int, b0: int, c0: int, d0: int, e0: int, f0: int) {
.B1:
  u0: int = add a0 b0;
  v0: int = add c0 d0;
  w0: int = add e0 f0;
  cond: bool = const true;
  br cond .B2 .B3;
.B2:
  x0: int = add c0 d0;
  y0: int = add c0 d0;
  jmp .B4;
.B3:
  u1: int = add a0 b0;
  x1: int = add e0 f0;
  y1: int = add e0 f0;
  jmp .B4;
.B4:
  u2: int = phi u0 u1 .B2 .B3;
  x2: int = phi x0 x1 .B2 .B3;
  y2: int = phi y0 y1 .B2 .B3;
  z0: int = add u2 y2;
  u3: int = add a0 b0;
}
```

My program outputs the following results, which match the expected output in the paper. We can see those operations that calculate the same value are eliminated in `B2` and `B3`, and those useless and redundant phi-nodes are also removed in `B4`.

```
@main(a0: int, b0: int, c0: int, d0: int, e0: int, f0: int) {
.B1:
  u0: int = add a0 b0;
  v0: int = add c0 d0;
  w0: int = add e0 f0;
  cond: bool = const true;
  br cond .B2 .B3;
.B2:
  jmp .B4;
.B3:
  jmp .B4;
.B4:
  x2: int = phi v0 w0 .B2 .B3;
  z0: int = add u0 x2;
  ret;
}
```