# Lesson 5 - Global Analysis

<!-- 
1. Implement some dominance utilities:
* Find dominators for a function.
* Construct the dominance tree.
* Compute the dominance frontier.
2. Devise a way to test your implementations. For example, is there a way you can algorithmically confirm that a block A dominates a block B? While computing these sets should be cheap, checking their output could use slow, naive algorithms.
-->

Please follow the instructions below to run the program.
```bash
bril2json < test/loopcond.bril | python3 dom.py
```

