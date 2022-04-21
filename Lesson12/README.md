# Lesson 12 - Dynamic Compilers

The task is to implement a trace-based speculative optimizer for Bril. You’ll implement the same concept as in a tracing JIT, but in a profile-guided AOT setting: profiling, transformation, and execution will be distinct phases. The idea is to implement the “heavy lifting” for a trace-based JIT without needing all the scaffolding that a complete JIT requires, such as on-stack replacement.

Concretely, there are two main phases:
* Modify the reference interpreter to produce traces.
* Build an optimizer that injects traces back into the original program using the speculation extension to provide a “fast path.”

Start by reading the documentation for the speculation extension (and watch the video!). That should give you an idea of what’s required to augment a program with a speculative execution of an extracted trace. Then make a plan for how you’ll hack the interpreter to produce one of those traces.

Here’s a recipe:
* Start interpreting normally.
* At some point during execution (at the very beginning of main, for example, or when reaching a backedge), start tracing.
* While tracing, record every instruction as it executes. Eliminate jumps; replace branches with guard instructions. Feel free to do the interprocedural version, and to bail out on any other instruction you don’t want to handle.
* Stop tracing at some point (after a fixed number of instructions, for example, or at the next backedge) and save the trace to a file.
* For bonus “points,” statically optimize the trace by eliminating instructions that depend on foregone conclusions enforced by guards.
* Transform the program to stitch the trace back into the program using speculate and commit instructions.
* Convince yourself that your tracing is correct by checking that the program does the same thing as the non-speculative version. Ideally, it should also execute fewer instructions.


Please follow the instructions below to run the program.
```bash
# tracing-based JIT
python3 bvm.py -f test/demo.json 42
# optimize the trace
python3 ../Lesson3/lvn.py -f trace.json | python3 ../Lesson3/dce.py | python3 ../Lesson3/lvn.py | python3 ../Lesson3/dce.py > trace.opt.json
# insert traced optimized path
python3 transform.py test/demo.json trace.opt.json
# reexecute optimized program
python3 bvm.py -f test/demo.opt.json 42
```

In this task, I continue using my [bril-py](https://github.com/chhzh123/bril-dev/blob/master/Lesson12/bvm.py) interpreter and build a tracing-based JIT on top of it. The main part of my JIT can be found [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson12/bvm.py#L210-L242). It is also very easy to add speculative execution support to my interpreter, which only needs to store the original data frame of the program and restore it when the guard function goes false. It takes less than 10 lines of [code](https://github.com/chhzh123/bril-dev/blob/master/Lesson12/bvm.py#L177-L185) to implement.


## Tracing-Based JIT
I simply start tracing from the beginning of the program and add instructions to the trace based on which operation the JIT meets:
* For `jmp`, we simply eliminate it, since we only generate straight-line codes.
* For `br`, we need to add a `guard` instruction to the trace, but the condition should be reverted first if we take the false branch, which means a `not` instruction is needed before the `guard` one.
* For `call`, the procedure is similar to function inlining (which I've done in [Lesson 2](https://github.com/sampsyo/cs6120/discussions/263#discussioncomment-2101320)). In the beginning, the arguments should be copied from the caller function using `id`, and the variables inside the callee function need to be renamed. There are no `call` instructions in the trace, and the code inside the function will be flattened into straight-line codes.
* For `ret`, we use `id` to copy the return value back to the caller function. These redundant instructions will be eliminated by a future DCE pass.
* All other instructions are directly added to the trace.

After we obtain the trace, we can call the LVN and DCE passes to optimize it. I then provide a [tranform.py](https://github.com/chhzh123/bril-dev/blob/master/Lesson12/transform.py) script to insert the trace back to the original program and add speculative markers to it. Since I trace the whole program, the whole trace can be directly put in front of the program. `guard`'s exit will become the beginning of the original program, and the next instruction of `commit` should be `jmp` to the end of the original program.

Finally, we can take the program with optimized trace and re-execute it.

## Testing
I again took several test programs from previous lessons, JIT executed, and observed their performance. For demonstration, I only use two test cases here.

The first case is the [example](https://www.cs.cornell.edu/courses/cs6120/2022sp/lesson/12/) on the class, which involves function calls (interprocedural optimization).
```
@f(a: int) :int {
  one: int = const 1;
  b: int = sub a one;
  ret b;
}

@g(a: int) :int {
  one: int = const 1;
  b: int = add a one;
  ret b;
}

@main(x: int) {
  one: int = const 1;
  y: int = add x one;
  cst: int = const 100;
  cond: bool = lt x cst;
  br cond .true .false;
.true:
  z: int = call @f y;
  jmp .exit;
.false:
  z: int = call @g y;
  jmp .exit;
.exit:
  print z;
}
```

After the trace was generated, I found it was very tricky to do optimization with [LVN](https://github.com/chhzh123/bril-dev/blob/master/Lesson3/lvn.py). Our previous implementation of LVN actually cannot work for this case, since not all the arguments in the instruction are constants. We cannot simply apply constant folding or constant propagation to this case. Some symbolic equivalence testing should be supported. For a simple workaround, I extend the LVN pass to let it check the former referenced instruction, and see if the previous one is a complementary instruction（e.g., `add` and `sub`, `mul` and `div`). If so, we further check if the second constants are the same. If they add and subtract the same constant, then we replace the latter instruction with an `id` instruction which directly copies the data from the original variable. With DCE, this case can be later eliminated.

```
y = x + 1;
a = y;
z = a - 1;
```

Finally, we obtain the program with optimized trace.
```
@main(x: int) {
  speculate;
  cst: int = const 100;
  cond: bool = lt x cst;
  guard cond .trace_entry;
  print x;
  commit;
  jmp .trace_exit;
.trace_entry:
  one: int = const 1;
  y: int = add x one;
  cst: int = const 100;
  cond: bool = lt x cst;
  br cond .true .false;
.true:
  z: int = call @f y;
  jmp .exit;
.false:
  z: int = call @g y;
  jmp .exit;
.exit:
  print z;
.trace_exit:
}
```

The result is shown below. We can see that the two programs indeed generate the same result, and our traced program has fewer instructions than the original one.
```bash
> python3 bvm.py -f test/demo.json 42
42
# of instructions: 11
> python3 bvm.py -f test/demo.opt.json 42
42
# of instructions: 7
```

But tracing the whole program incurs overheads. If we switch to another value no smaller than 100, we may need to speculatively execute the traced code first, and then roll back to the beginning of the program and execute again. So in this case, the number of executed instructions increases.
```bash
> python3 bvm.py -f test/demo.json 42
42
# of instructions: 11
> python3 bvm.py -f test/demo.opt.json 100
102
# of instructions: 15
```

The second case involves a loop. The test program can be found [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson12/test/loopcond.json). The traced program is exactly the same as loop unrolling, so no loop overhead is introduced after tracing. The number of instructions is greatly reduced as shown below, which shows the effectiveness of my JIT compiler. However, the downside of this is that the size of the generated program will be large, but it can be tackled by changing the starting point of the trace to the beginning of the loop.

```bash
> python3 bvm.py -f test/loopcond.json
1984
# of instructions: 117
> python3 bvm.py -f test/loopcond.opt.json
1984
# of instructions: 79
```