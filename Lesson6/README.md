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
bril2json < test/ssa/loop-ssa.bril | python3 to_ssa.py | bril2txt

# test
make test
```

<!-- https://groups.seas.harvard.edu/courses/cs153/2018fa/lectures/Lec23-SSA.pdf
https://www.cs.princeton.edu/courses/archive/spr04/cos598C/lectures/11-SSA-3x1.pdf
https://www.ics.uci.edu/~yeouln/course/ssa.pdf
-->

In this assignment, I implemented the "into SSA" and "out of SSA" transformations, and tested them using `turnt`. Code can be found in my [repository](https://github.com/chhzh123/bril-dev/tree/master/Lesson6).

## Converting to SSA
There are two steps in the SSA algorithm, the first one is phi-node insertion, and the second one is variable renaming. The pseudocode is very concise and miss lots of details. I was also confused about the phi-node part of the insertion algorithm in the first place, and was misled that we insert an argument to the phi-node when we traverse the dominance frontier of `def`. Considering the following code that can bypass `x` from the `.entry` block to the `.end` block, we may probably get the phi-node with only one argument from `.left` since `.end` only in `.left`'s dominance frontier but not in `.entry`'s (which is an empty set).
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

The renaming part is also tricky with several details need to be paid attention to. For replacing the argument names, I added a constraint of not modifying the phi-node arguments. Since some of the phi-node arguments have already been written by the predecessor blocks, it will be overwritten if we do not distinguish the phi-node with other opertions.

The phi-node renaming is probably the most confusing part -- "assuming p is for a variable v, make it read from stack[v]" -- the pseudocode does not tell us which phi-node argument we should modify and how to do that. I finally found some clues from this [lecture note](https://www.ics.uci.edu/~yeouln/course/ssa.pdf) -- "replace the `j`-th operand of `RHS(p)` by `Top(Stacks[v])`", where "`j` is the position in `s`’s phi-function corresponding to block b". So we know we can replace the `j`-th operand of the phi-node by the top of the stack. If the stack is empty, then it means the value comes from a branch that has no definitions of that variable, so that operand should be set as `__undefined`.

Lastly, I added some enhancements to my SSA algorithm in order to pass *all* the test cases:
* Add my entry block at the beginning of the program (`while.bril`). This is always useful especially for the program whose entry block is the header of a loop (which has a backedge). If the entry block is empty without doing any computation, I will eliminate it in the end.
* Support function arguments (`argwrite.bril`). This only needs to add those arguments into variable stack at initialization.
* Support multiple functions (`loop-branch.bril`). Traverse all the functions and run SSA algorithm for each of them.
* Type specification (`loop.bril`). The pseudocode does not mention anything about variable type, but to generate correct phi-node, we need to preserve the type information, so we can basically add types into the variable definition map.
* Support phi node in the original program (`if-ssa.bril`). I rename the original `phi` node to `phi_` so that it can be viewed as normal operations whose arguments will be replaced by the top name of the stack. Finally, the `phi_` operation will be changed back to `phi` in order to be parsed by `brili`.

## Converting from SSA
This is much easier than SSA convertion.

insert before jmp/br function