# Lesson 2 - Bril

## Benchmark
I implemented a graph format converter as a benchmark in this [PR](https://github.com/sampsyo/bril/pull/146). It transforms a graph in [adjacency matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) format (dense representation) to [Compressed Sparse Row (CSR)](https://en.wikipedia.org/wiki/Sparse_matrix) format (sparse representation). It intensively uses the memory facility of Bril and mimics the behavior of multi-dimensional arrays.

The input graph is randomly generated reusing the algorithm in `benchmark/mat-mul.bril`. Basically, users can input the number of nodes and a fixed seed to the program, and the program will output the adjacency matrix, the CSR offset array, and the CSR edges array.


## Bril Tool
This subproject implements a **function inlining** pass (written in Python) for Bril, which basically puts all the function calls inside the main function. It is an important compiler optimization that eliminates the overheads of maintaining stacks for function calls.

An example can be executed using the following command.
```bash
# transform the code and execute program
bril2json < test/call-with-args.bril | python3 function_inlining.py | brili

# or output the transformed code
bril2json < test/call-with-args.bril | python3 function_inlining.py | bril2txt
```

At the very beginning, people may think function inlining is just about moving the whole function body to the main function, but actually it needs more consideration. In general, I did the following two things in my pass:

1. Replace variable references.
I constructed a mapping from local variables (function arguments) to global variables. Since the function signature and the return value will be removed after the function body is inserted into the main function, those input and output variables should be replaced with variables in the main function.
* For operands/inputs, we need to check the `"args"` field, traverse all the arguments, and replace those in the function signature.
* For returns/outputs, we should first take out all the `ret` instructions and see what they return. This is because in a function we may have multiple places to return a value, which is not necessary at the end of the function. Those variables should all be replaced as the `"dest"` one of the call function. Moreover, since this actually involves storing values into memory, we should be very careful about whether they replace the previous useful values, so this comes to the second issue.

2. Resolve naming conflicts.
It would be simple if users strictly use different variable names in different places, but this is not always the case. For example, we may use `i` as the iteration variable in all the loops, thus this may possibly lead to naming issues that the variable refers to is not what we want. In my implementation, I used a simple naming rule to resolve the conflicts.
* For variables inside the function, I added `_fvar` behind the original variable name and further added function ID behind this in order to avoid the same names across different functions.
* For labels, I also added `_flabel` behind the original name, so that the control flow may not be confused about where to go.

An example program here shows how my pass works.
```bril
@main {
  x: int = const 2;
  y: int = const 2;
  z: int = call @add2 x y;
  print y;
  print z;
}

@add2(x: int, y: int): int {
  w: int = add x y;
  y: int = const 5;
  print y;
  print w;
  ret w;
}
```

We can see that from the following output, there is the only main function. Those variables inside the function are renamed, and no return instructions are involved. But there is also another issue, if we look at the original program, we can see the outer variable `y` is actually shadowed by the function argument `y`, although they have the same name. This may cause problems when `y` inside the function is reassigned, i.e. the scope of the inner `y` is only inside the function and should not affect the value of the outer `y`. So we should carefully distinguish the variables here and use different names for variables in different scopes (`y_fvar0`), which somehow mimics the stack that protects the contexts in between the function.
```bril
@main {
  x: int = const 2;
  y: int = const 2;
  z: int = add x y;
  y_fvar0: int = const 5;
  print y_fvar0;
  print z;
  print y;
  print z;
}
```

After we resolve the above issues, we can finally create a main function that takes in all the function bodies.

I also added five test cases in my test folder and used `turnt` to test if my pass runs correctly.


### Limitations
There is one limitation here -- my pass can only work with the function calls in the main function and cannot support arbitrarily nested function calls. Since for recursive functions, we do not know when it exactly stops, which is runtime information and cannot be obtained during compile time. Thus, as a simple solution, I directly raised a runtime error if some functions have nested function calls.


### Implementation Details
A good practice is to first check if the key of an operation exists. For example, labels do not have an `"op"` key. `"args"` and `"dest"` does not always exist either.


### Discussions
Please find detailed discussions on the [course webpage](https://github.com/sampsyo/cs6120/discussions/263#discussioncomment-2101320).

1. I am not sure why for some operations in Bril, they have a parameter list to store the item. For example, the `call` operation has a field called `"funcs"` and takes in a list of functions, but I have no idea how this can work for multiple functions. Another one is `ret`, which also has a `"args"` list. If the Bril IR is in SSA form, then I think it cannot have multiple return values?

2. Declaration and assignment. I am not sure why the following code can pass the compilation and execute. As I know, Bril has no type casting operators, so how can this be doable conversing from `int` to `bool` and back to `int`. Are there any implicit type casting rules like those in C/C++? Also, does `x: bool = const 0;` mean *declaring* a new variable or *assigning* a new value to the original variable? The vague semantics makes transformation pass hard to be done correctly in some ways.

```bril
@main() : int {
  x: int = const 190;
  x: bool = const 0;
  print x;
  ret x;
}
```