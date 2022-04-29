# Lesson 13 - Program Synthesis

* Follow the synthesis tutorial in your favorite language to build a sketch-based expression synthesis engine. You can use Python and Z3 directly, as in Adrian’s tutorial, or try Rosette, as in James Bornholt’s tutorial.
* Add an extension to generate more complex expressions than the ternary and bit-shift expressions from the tutorial. Get creative!
* Write a couple of example sketches that show off your new language extension, and report on how hard it was to get the solver to discharge them.

```bash
python3 syn.py sketches/s1.txt
```

In this task, I implemented a simple solver for polynomial factoring on the integer set ![Z](https://render.githubusercontent.com/render/math?math=\mathbb{Z}). The code is [here](https://github.com/chhzh123/bril-dev/blob/master/Lesson13/syn.py), which partly reuses the [Ex2](https://github.com/sampsyo/minisynth/blob/master/ex2.py) program.

Firstly I added power support (`a^b`) to the language, so that the users can type the polynomial they want to factorize in a text file. We can consider the following polynomial,
![poly](https://render.githubusercontent.com/render/math?math=f(x)=a_nx^n%2Ba_{n-1}x^{n-1}%2B\cdots%2Ba_0),
if
![poly](https://render.githubusercontent.com/render/math?math=\forall{r},f(r)=0\implies{r\in\mathbb{R}}),
then we can rewrite ![poly](https://render.githubusercontent.com/render/math?math={f(x)}) in this form
![expr](https://render.githubusercontent.com/render/math?math=f(x)=g(x)(h_0x%2Bh_1)%2B(h_2x%2Bh_3)%2B\cdots%2B(h_{2n}x%2Bh_{2n%2B1}),h_i\in\mathbb{Z}).
Those ![hi](https://render.githubusercontent.com/render/math?math=h_i) are the variables we want to solve.

After my synthesizer reads in the original polynomial, it will automatically construct the above ![hi](https://render.githubusercontent.com/render/math?math=h_i) expression based on the largest exponent of the polynomial. The polynomial factoring problem then becomes finding the solution of ![fgx](https://render.githubusercontent.com/render/math?math={f(x)}\equiv{g(x)}).

Since I used `^` as the power operator in the language, but for Python `^` represents XOR, we need to add paratheses to ensure the precedence relationship is correct. (I spent lots of time debugging here :(

Finally the synthesizer works as expected. I show two non-trivial examples below, both of which prove the correctness of my synthesizer. However, when the exponent term is greater than 3, it has already taken more than 20 minutes to get the solution on my M1 MacBook.

```cpp
// example 1
(((x ^ 3) + (6 * (x ^ 2))) + (11 * x)) + 6
(((1 * x) + 1) * ((1 * x) + 2)) * ((1 * x) + 3)
// example 2
((((x ^ 4) + (x ^ 3)) - (19 * (x ^ 2))) + (11 * x)) + 30
((((1 * x) + 1) * ((1 * x) + -2)) * ((1 * x) + 5)) * ((1 * x) + -3)
```

In the first place I wanted to implement the general factorization algorithm as the one shown in [Mathematica](https://reference.wolfram.com/language/ref/Factor.html.en?source=footer), but it becomes very complicated when the roots of the polynomial are in complex space ![c](https://render.githubusercontent.com/render/math?math=\mathbb{C}). Since Z3 is actually not a general symbolic solver, the search space is too large for it to deal with more complex factorization problem.