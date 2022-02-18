# Lesson 4 - Dataflow Analysis

<!-- 
Implement at least one data flow analysis. You choose which.
For bonus “points,” implement a generic solver that supports multiple analyses.
-->

Please follow the instructions below to run the program.
```bash
bril2json < test/sign.bril | python3 dfa.py -sign
```

I implemented a **generic** dataflow analysis framework that enables users to easily plug in different algorithms. My code can be found [here](https://github.com/chhzh123/bril-dev/tree/master/Lesson4), and tests are in the `test` folder. Based on this framework, I implemented several analysis passes below:
  - [Reaching definitions](#reaching-definitions)
  - [Live variables](#live-variables)
  - [Uninitialized variables](#uninitialized-variables)
  - [Sign analysis](#sign-analysis)

Since I have implemented [constant propagation](https://github.com/sampsyo/cs6120/discussions/284#discussioncomment-2147718) with simple control flow last time, and I think it is relatively straightforward to do that within the dataflow framework (which essentially needs to plug LVN into the transfer function), I didn't pay lots of effort on that. Instead, I tried to implement the uninitialized variables and sign analysis, which are not directly covered in the lecture but are widely used in static analysis.


## Reaching definitions
This is the textbook algorithm but is still somehow tricky since it actually works on instructions/definitions instead of variables. Therefore, the [implementation](https://github.com/sampsyo/bril/blob/main/examples/df.py#L142-L147) in class is not completely correct, which also obfuscates with live variables.

To get the correct definition references, we need to first label those definitions. I used `d#id_<var>` to label the definitions in order to distinguish different definitions referring to the same variable. In this way, I can easily take the variable name after the underscore When examining whether a variable is killed or not.

I also added support for function arguments, which should be added to initial definitions.


## Live variables
The provided tranfer function is correct in general but requires more consideration when implementation. Considering the following example, if using the transfer function `in_b = use_b U (out_b - def_b)`, we can get `out_b=∅`, `def_b={d}`, and `use_b={a,c,d}`, therefore `in_b={a,c,d}`. This is because `d` is defined in this basic block and immediately used later, but it should not be considered as alive before this block.

```
.end:
  d: int = sub a c;
  print d;
```

To fix this problem, we should do the *instruction-wise* analysis, meaning Set `in` and `out` should actually hold for each instruction.

```
i2-> d: int = sub a c;
i1-> print d;
```

By traversing the instructions from back to front, we have `out[i2]=in[i1]={d}`, and then `in_b=in[i2]={a,c}U({d}-{d})={a,c}`, which is the correct answer. Also, considering some instructions may have read and write to the same variable (e.g. `result: int = mul result i`), we should first remove the uses (`"dest"`) and add the references (`"args`) to the Set.

In summary, this example shows sometimes the transfer function should be applied per instruction instead of per block. Otherwise, it may lead to a different result.


## Uninitialized variables
This algorithm tries to examine whether there exist uninitialized variables in the program. I take all the variables and make them uninitialized at the beginning. When some variables are defined in the block, they are removed from the Set.
```
@main(cond: bool) {
  br cond .left .right;
.left:
  a: int = const 1;
  b: int = const 5;
  jmp .end;
.right:
  a: int = const 2;
  c: int = const 10;
  jmp .end;
.end:
  d: int = sub a c;
  e: int = add b c;
  print d;
}
```

Take the above program as an example, this analysis can capture all the uninitialized variables from different paths. Although `c` is defined in `.right`, it is not defined in `.left`, thus my pass views it uninitialized in the block `.end`. On the contrary, `a` is defined in both of the branches, so it is initialized in the `.end` block.
```
b1:
  in:  a, b, c, d
  out: a, b, c, d
left:
  in:  b, c, a, d
  out: c, d
right:
  in:  b, c, a, d
  out: b, d
end:
  in:  b, c, d
  out: b, c
```

Actually, this piece of program is valid in Python, since Python does not have this kind of static analysis to check whether a variable is initialized in all the paths. But for C/C++, this should be an obvious error that will be captured during compile-time.


## Sign analysis
For sign analysis, it basically determines the sign of each variable. I used the [lattice definition](https://lara.epfl.ch/w/_media/sav08:schwartzbach.pdf), except for `0`, `+`, and `-`, there are two more elements -- `⊥` means the undefined values, and `T` means unknown values that can have different signs.

For example, for the add operation, the sign analysis should follow the below computation rule.

| **add** | **⊥** | **0** | **-** | **+** | **T** |
| :--: | :--: | :--: | :--: | :--: | :--: |
| **⊥** | ⊥ | ⊥ | ⊥ | ⊥ | ⊥ |
| **0** | ⊥ | 0 | - | + | T |
| **-** | ⊥ | - | - | T | T |
| **+** | ⊥ | + | T | + | T |
| **T** | ⊥ | T | T | T | T |

I only defined the rules for arithmetic operations like `add`, `sub`, `mul`, and `div`. A simple example is shown below.
```
@main {
  a: int = const 10;
  b: int = const -5;
  cond: bool = const true;
  br cond .left .right;
.left:
  c: int = add a b;
  d: int = mul a b;
  jmp .end;
.right:
  one: int = const 1;
  c: int = add a one;
  jmp .end;
.end:
  print c;
}
```

The analysis outputs the following signs. We can see that `c` is `+` in `.right` but is `T` in `.left`, so after merging, the sign of `c` is `T`.
```
b1:
  in:  {'a': '⊥', 'b': '⊥', 'cond': '⊥', 'c': '⊥', 'd': '⊥', 'one': '⊥'}
  out: {'a': '+', 'b': '-', 'cond': '+', 'c': '⊥', 'd': '⊥', 'one': '⊥'}
left:
  in:  {'a': '+', 'b': '-', 'cond': '+', 'c': '⊥', 'd': '⊥', 'one': '⊥'}
  out: {'a': '+', 'b': '-', 'cond': '+', 'c': 'T', 'd': '-', 'one': '⊥'}
right:
  in:  {'a': '+', 'b': '-', 'cond': '+', 'c': '⊥', 'd': '⊥', 'one': '⊥'}
  out: {'a': '+', 'b': '-', 'cond': '+', 'c': '+', 'd': '⊥', 'one': '+'}
end:
  in:  {'a': '+', 'b': '-', 'cond': '+', 'c': 'T', 'd': '⊥', 'one': '⊥'}
  out: {'a': '+', 'b': '-', 'cond': '+', 'c': 'T', 'd': '⊥', 'one': '⊥'}
```

Sign analysis actually does a similar thing of finding uninitialized variables. Once the sign of a variable is `⊥` in some blocks, it means the variable is undefined from some execution paths.