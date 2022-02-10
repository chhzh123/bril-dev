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
