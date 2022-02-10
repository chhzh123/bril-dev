# Lesson 3 - DCE/LVN

## Dead Code Elimination (DCE)

DCE is relatively easy to implement, just following the pseudocode would be fine:
1. Traverse all the arguments of instructions to get the used list (stored in a set)
2. Traverse again to check whether the `dest` of instructions are in used list. If not, remove the instruction.
3. For the case of reassignment, first check the used list, and then check the definition list, and only retain the last definition.
4. Remember to iterate the algorithm until it converages.

The following shows the test status of the benchmarks from `examples/test/tdce`.

| Benchmark         | Status | Comments |
| :--:              | :--:   | :--: |
| `combo`             | :heavy_check_mark: |
| `diamond`           | :x:    | Control flow |
| `double-pass`       | :heavy_check_mark: | Same as `double-pass`, Original test incorrect |
| `double`            | :heavy_check_mark: |
| `reassign-dkp`      | :heavy_check_mark: |
| `reassign`          | :heavy_check_mark: | Same as `reassign-dkp`, Original test incorrect |
| `simple`            | :heavy_check_mark: |
| `skipped`           | :x:     | Control flow |


## Local Variable Numbering (LVN)

LVN is much tricky somehow and requires careful considerations. I use a list to store the LVN table. Each element is a tuple containing the value and the canonical name. This takes O(1) to access a row by index, but takes O(n) in the worst case to find a value. I am not sure if there is data structure can enjoy both of the world that seaching by index and searching by key can both achieve constant time (if not storing redundant data). It would be helpful to reduce the searching overheads if the program has lots of instructions.

Based on LVN, I implemented all the three (1) common subexpression elimination, (2) copy propagation, and (3) constant propagation/folding. (1) only needs to follow the LVN algorithm and checks if the value is computed before, and then replace it. (2) is also straightforward that needs to find the initial definition of the variable. (3) is a little bit tricky. What I do is writing specific computation rules for each arthimetic operations, but it is very inconvenient and the if-else cases take almost 1/3 part of the code. Also, to make constants pass the program from top to bottom, I iterate the algorithm several times till the program does changed just like what we did in DCE.

The attached [pesudocode](https://www.cs.cornell.edu/courses/cs6120/2022sp/lesson/3/) is actually a simplified version of the LVN algorithm. In my implementation, I pay more attention to the following things:
<!-- For `add` and `mul` I directly sorted the arguments, but be careful that `sub` does not have the communitivity. -->
* Function arguments should be also added to the LVN table before traversing the instructions.
* For constructing fresh variable name, I recorded a global counter and attached that number behind the variable names in order to prevent further name conflicts. For example, the original variable name is `x`, then the new name will be `x_new0`.
* If the instructions will be overwritten later, we should also not only update the argument names, but also update the latter instructions (before next definition) that contain this variable. Otherwise, we may not find the requested variable in the `var2num` dict.

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
