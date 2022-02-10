# Lesson 3 - DCE/LVN

<!-- In your summary on the GitHub Discussions thread, briefly write up the evidence you have that your LVN implementation is correct and actually optimizes programs.
For bonus “points,” extend your LVN implementation to optimize the trickier examples given in class. -->

Please follow the instructions below to run the program.
```bash
bril2json < test/lvn/complex.bril | python3 lvn.py | python3 dce.py | bril2txt
```

## Dead Code Elimination (DCE)

DCE is relatively easy to implement, just following the pseudocode would be fine:
1. Traverse all the arguments of instructions to get the used list (stored in a set)
2. Traverse again to check whether the `dest` of instructions are in used list. If not, remove the instruction.
3. For the case of reassignment, first check the used list, and then check the definition list, and only retain the last definition.
4. Remember to iterate the algorithm until it converges.

The following shows the test status of the benchmarks from `examples/test/tdce`.

| Benchmark         | Status | Comments |
| :--:              | :--:   | :--: |
| `combo`             | :heavy_check_mark: |
| `diamond`           | :x:    | Control flow (br) |
| `double-pass`       | :heavy_check_mark: | Same as `double-pass`, original test incorrect |
| `double`            | :heavy_check_mark: |
| `reassign-dkp`      | :heavy_check_mark: |
| `reassign`          | :heavy_check_mark: | Same as `reassign-dkp`, original test incorrect |
| `simple`            | :heavy_check_mark: |
| `skipped`           | :heavy_check_mark: | Control flow (jmp), remove dead blocks |


## Local Variable Numbering (LVN)

LVN is much tricky somehow and requires careful considerations. I use a list to store the LVN table. Each element is a tuple containing the value and the canonical name. This takes O(1) to access a row by index but takes O(n) in the worst case to find a value. I am not sure if there is data structure that can enjoy both of the world -- searching by index and searching by key can both achieve constant time (if not storing redundant data). It would be helpful to reduce the searching overheads if the program has lots of instructions.

Based on LVN, I implemented all three (1) common subexpression elimination, (2) copy propagation, and (3) constant propagation/folding. (1) only needs to follow the LVN algorithm and check if the value is computed before, and then replace it. (2) is also straightforward that needs to find the initial definition of the variable. (3) is a little bit tricky. What I do is write specific computation rules for each arithmetic operation, but it is very inconvenient and the if-else cases take almost 1/3 part of the code. Also, to make constants pass through the program from top to bottom, I iterate the algorithm several times until the program does not changed just like what we did in DCE.

The attached [pesudocode](https://www.cs.cornell.edu/courses/cs6120/2022sp/lesson/3/) is actually a simplified version of the LVN algorithm. In my implementation, I pay more attention to the following things:
<!-- For `add` and `mul` I directly sorted the arguments, but be careful that `sub` does not have the communitivity. -->
* Function arguments should be also added to the LVN table before traversing the instructions.
* For constructing a fresh variable name, I recorded a global counter and attached that number behind the variable names in order to prevent further name conflicts. For example, the original variable name is `x`, then the new name will be `x_new0`.
* If the instructions will be overwritten later, we should also not only update the argument names, but also update the latter instructions (before the next definition) that contain this variable. Otherwise, we may not find the requested variable in the `var2num` dict.

The following shows the test status of the benchmarks from `examples/test/lvn`.

| Benchmark         | Status | Comments |
| :--:              | :--:   | :--:     |
| `clobber-fold`      | :heavy_check_mark: |
| `clobber`           | :heavy_check_mark: | Same as `clobber-fold` |
| `commute`           | :heavy_check_mark: |
| `divide-by-zero`    | :heavy_check_mark: |
| `fold-comparisons`  | :heavy_check_mark: | Original test incorrect |
| `idchain-nonlocal`  | :x: | Control flow |
| `idchain-prop`      | :heavy_check_mark: |
| `idchain`           | :heavy_check_mark: | Same as `idchain-prop` |
| `logical-operators` | :heavy_check_mark: |
| `nonlocal`          | :x: | Control flow |
| `reassign`          | :heavy_check_mark: |
| `redundant-dce`     | :heavy_check_mark: |
| `redundant`         | :heavy_check_mark: |
| `rename-fold`       | :heavy_check_mark: |


## Correctness
Apart from the above tests given in the bril repository, I also wrote additional test cases to test the correctness of my algorithms. The result of LVN is passed to DCE to do further optimization. All the cases are tested using `turnt`, including the trickier example given in class.

Here I give another example to show how my passes work, and it should cover all the cases in LVN and DCE.
```
@main {                                        
  x: int = const 14;                           
  y: int = const 2;                            
                                               
  # constant propagation                       
  div_xy: int = div x y;                       
                                           # lvn
  # copy propagation                       @main {
  div_xy2: int = id div_xy;                  x: int = const 14;                        
                                             y_new0: int = const 2;            # lvn + dce        
  # dead code                                div_xy: int = const 7;            @main {
  add_xy: int = add x y;                     div_xy2: int = div div_xy;          y_new1: int = const 8;
                                             add_xy: int = const 16;             print y_new1;
  # common subexpression elimination         mul_xy: int = const 49;             y: int = const 10;
  mul_xy: int = mul div_xy div_xy2;          y_new1: int = const 8;              print y;
                                             print y_new1;                       sub_xy: int = const -39;
  # reassignment                             y: int = const 10;                  print sub_xy;
  y: int = const 8;                          print y;                            equality: bool = const true;
  print y;                                   sub_xy: int = const -39;            print equality;
                                             print sub_xy;                     }
  # double reassignment                      result: int = const -39;                  
  y: int = const 10;                         equality: bool = const true;              
  print y;                                   print equality;                           
                                           }
  # further propagation                        
  sub_xy: int = sub y mul_xy;                  
  print sub_xy;                                
                                               
  # constant folding                           
  result: int = const -39;                     
  equality: bool = eq sub_xy result;           
  print equality;                              
}
```

Using this testbench, I also found a subtle mistake that I should use `//` to implement integer division and `/` to implement floating-point division. We do not record data types in the LVN table, but it indeed matters when doing constant folding.
