# Bril-Dev

This repository contains experimental tools of the [Bril](https://github.com/sampsyo/bril) compiler for Cornell [CS 6120 (Spring 2022)](https://www.cs.cornell.edu/courses/cs6120/2022sp).


## Lessons
* Lesson 1: Intro & Paper Claiming
* Lesson 2: [Bril](Lesson2)
* Lesson 3: [DCE/LVN](Lesson3)
* Lesson 4: [Dataflow Analysis](Lesson4)
* Lesson 5: [Global Analysis](Lesson5)
* Lesson 6: [SSA](Lesson6)
* Lesson 7: [LLVM](Lesson7)
* Lesson 8: [Loop Optimization](Lesson8)
* Lesson 9: Interprocedural Analysis
* Lesson 10: Alias Analysis
* Lesson 11: [Memory Management](Lesson11)
* Lesson 12: [Dynamic Compilers](Lesson12)
* Lesson 13: [Program Synthesis](Lesson13)
* Lesson 14: Concurrency & Parallelism


## Build
```bash
git clone https://github.com/sampsyo/bril.git
cd bril-ts
yarn
yarn build
yarn link
export PATH=$(yarn global bin):$PATH

cd ..
python3 -m venv ~/.venv/bril-dev
source ~/.venv/bril-dev/bin/activate
pip install flit
flit install --symlink

pip install turnt
make test
```

## Run
```bash
bril2json < test.bril
python3 xxx.py # some passes
brili ... # generated json files
bril2txt ... # check the IR code
```