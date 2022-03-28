# Lesson 9 - Memory Management

* Implement a garbage collector for the Bril interpreter and the Bril memory extension, eliminating the need for the free instruction. Stick with something simple, like reference counting or a semispace collector.
* Check that it works by running the benchmarks that use memory after deleting all their free instructions.

Please follow the instructions below to run the program. The basic skeleton program comes from the course [repository](https://github.com/sampsyo/llvm-pass-skeleton).
```bash
mkdir build
cd build
cmake ..
make

cd ../test
make opt
```
