# Lesson 6 - SSA

<!-- 
* Implement the “into SSA” and “out of SSA” transformations on Bril functions.
** One thing to watch out for: a tricky part of the translation from the pseudocode to the real world is dealing with variables that are undefined along some paths.
** Previous 6120 adventurers have found that it can be surprisingly difficult to get this right. Leave yourself plenty of time, and test thoroughly.
* As usual, convince yourself that your implementation actually works!
** You will want to make sure the output of your “to SSA” pass is actually in SSA form. There’s a really simple is_ssa.py script that can check that for you.
** You’ll also want to make sure that programs do the same thing when converted to SSA form and back again. Fortunately, brili supports the phi instruction, so you can interpret your SSA-form programs if you want to check the midpoint of that round trip.
* For bonus “points,” implement global value numbering for SSA-form Bril code.
-->

Please follow the instructions below to run the program.
```bash
bril2json < test/..bril | python3 to_ssa.py
```

<!-- https://groups.seas.harvard.edu/courses/cs153/2018fa/lectures/Lec23-SSA.pdf
https://www.cs.princeton.edu/courses/archive/spr04/cos598C/lectures/11-SSA-3x1.pdf -->