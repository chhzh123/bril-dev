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
