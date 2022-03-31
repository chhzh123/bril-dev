# Lesson 9 - Memory Management

* Implement a garbage collector for the Bril interpreter and the Bril memory extension, eliminating the need for the free instruction. Stick with something simple, like reference counting or a semispace collector.
* Check that it works by running the benchmarks that use memory after deleting all their free instructions.

Please follow the instructions below to run the program.
```bash
python3 bvm.py -f test/bubblesort.json 5 10 7 5 1 3
```

Since I am an aficionado of Python, I did not use the TypeScript-based interpreter for this task. Instead, I built a **Python-based Bril interpreter** `bril-py` and implemented the garbage collector in that **Bril Virtual Machine (BVM)** :) Actually, BVM is very straightforward to implement, and it did not take me much time to make the whole thing work. The code can be found [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson9/bvm.py), which is very concise and less than 200 lines.

## Bril-py Interpreter
Using `bril2json`, we can obtain the JSON representation of the Bril program, which can be directly used as the input of the interpreter. Basically, the interpreter is a [stack machine](https://en.wikipedia.org/wiki/Stack_machine), but since the instructions in JSON representation have already had the operand information, we do not need to evaluate the expressions using a real stack, which greatly simplifies the work of the interpreter. However, a *frame stack* is needed to maintain the context of a function. I created a `Frame` class to record the data, instructions, and blocks in the function.

The virtual machine takes the `main` function as the top-level, append the arguments into the frame as initial data, and then starts evaluating the frame. The `eval_frame` function is essentially a dispatcher that takes in an instruction and calls the corresponding function to evaluate the instruction. Except for common binary instructions and control flow instructions (`jmp` and `br`), there are two more things to mention:

1. Function calls may trigger creating a new frame, and the new frame will be pushed into the frame stack to evaluate. The frame will be popped out and destroyed when the function returns. This is also where memory management (garbage collection) happens.
2. Due to time limitations, I did not use heap to model the dynamically allocated memory. Instead, I used a simple linear memory model to simulate memory allocation. I also added a memory leakage detector in my interpreter, so if there exists some memory that is not freed by the end of the program, my interpreter will throw an error. Similar to the double `free` cases, it will also raise an error.

I used the tests in previous assignments to test the correctness of my interpreter, and they all perform well and output the same results as the original Bril interpreter.

## Garbage Collector
After I built the bril-py interpreter, the garbage collector can be easily plugged into it. I implemented a reference counting garbage collector. Only several instructions may cause the references to change:
* `alloc`: Set the reference count of the allocated memory as 1. But if the variable overwrites the previous memory as shown in the following case, the reference count of the previous memory should be firstly decremented.
    ```
    one: int = const 1;
    a: ptr<int> = alloc one;
    a: ptr<int> = alloc one;
    ```
* `free`: This directly set the reference count of the memory to 0, but should not be used with automatic garbage collection.
* `ptradd`: This also leads to the reference count of the memory that the base pointer points to. Also be careful about the reassignment that may cause the original pointer invalid.
* `id`: If the operand is a pointer, the reference count is simply incremented by 1.
* `ret`: Those memory allocated in the function should be freed when they leave the function scope. There is one exception: if the function returns a pointer to allocated memory, then this pointer should not be freed.
    ```
    @foo : ptr<int> {
      one: int = const 1;
      p: ptr<int> = alloc one;
      ret p;
    }

    @main {
      p : ptr<int> = call @foo;
    }
    ```

I removed the `free` instructions from the Bril program and tested if the garbage collector works correctly. Those test examples can be found in the `test` folder. Some of them are from previous assignments, and some of them are from the bril `benchmark`. The output is the same as the original one, showing my garbage collector can indeed automatically manage memory.

In the beginning, I wanted to do something fancier, but I found Bril did not have those advanced language features, so even having a strong garbage collector, there are no test programs in Bril that can leverage these features. For example, I had a hard time thinking about how to construct a reference cycle in Bril, but later I found it seems it is impossible since Bril does not have OOP facilities and does not allow pointers pointing to pointers. For a similar reason, tracing garbage collectors may not be that useful. Common Bril program can be executed in less than one hundred lines, and function calls are also very limited, which means most of the garbage collection can be done when the function returns.