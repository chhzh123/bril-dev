# Lesson 9 - Memory Management

* Implement a garbage collector for the Bril interpreter and the Bril memory extension, eliminating the need for the free instruction. Stick with something simple, like reference counting or a semispace collector.
* Check that it works by running the benchmarks that use memory after deleting all their free instructions.

Please follow the instructions below to run the program.
```bash
python3 bvm.py -f test/bubblesort.json 5 10 7 5 1 3
```

Since I am an aficionado of Python, I do not use the TypeScript-based interpreter for this task. Instead, I built a **Python-based Bril interpreter** `bril-py` and implemented the garbage collector in that **Bril Virtual Machine (BVM)** :) Actually BVM is very straightforward to implement, and it does not take me much time to make the whole thing work. The code can be found [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson9/bvm.py) and is less than 200 lines.

## Bril-py Interpreter
Using `bril2json`, we can already obtain the JSON representation of the Bril program, which can be directly used as an intermediate representation or the input of the interpreter. Basically the interpreter is a [stack machine](https://en.wikipedia.org/wiki/Stack_machine), but since the instructions in json representation has already had the operand information, we do not need to evalute the expressions using a real stack, which greatly simplifies the work of the interpreter. However, a *frame stack* is needed to maintain the context of a function. I created a `Frame` class to record the data, instructions, and blocks in the function.

The virtual machine takes the main function as the top level, append the arguments into the frame as initial data, and then start evaluating the frame. The `eval_frame` function is essentially a dispatcher that takes in an instruction and calls the corresponding function to evaluate the instruction. Except for common binary instructions and control flow instructions (`jmp` and `br`), there are two more things to mention:

1. Function calls may trigger creating a new frame, and the new frame will be pushed into the frame stack to evaluate. The frame will be popped out and destroyed when the function returns. This is also where the memory management (garbage collection) happens.
2. Due to time limitation, I do not use heap to model the dynamically allocated memory. Instead, I use a simple linear memory model to simulate memory allocation. I also added a memory leakage detector in my interpreter, so if there exists some memory that is not freed by the end of the program, my interpreter will throw an error. Similar to the double free cases, it will also raise the error.

I used the tests in previous assignments to test the correctness of my interpreter, and they all perform well and outputs the same results as the original Bril interpreter.

## Garbage Collector
Bril does not have OOP facilities, and does not have garbage collection.
no cycles, no references, no pointers

tracing garbage collection is not that useful