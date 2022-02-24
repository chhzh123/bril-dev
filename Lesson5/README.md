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

In this task, I implemented several utility functions to construct the following sets of nodes based on the definitions:
* Dominators
* Strict dominators
* Immediate dominators
* Dominator tree
* Dominance frontier

All of them are very straightforward. Code can be found in my [repository](https://github.com/chhzh123/bril-dev/tree/master/Lesson5).


## Dominators
The update rule of the dominator is very simple, and I can write it using higher-order functions (`functool.reduce`) in one line in Python. However, I didn't make the whole algorithm correct in the first place since I naturally initialized all the dominator sets as empty. But the correct way should be initializing the dominator of the entry block as itself, and setting all blocks as dominators for all other blocks. (I noticed someone had the same mistake as mine on Zulip:) )

Another tricky thing here is that I first thought entry block should be the block that has no predecessors, but later I found I was wrong -- if the entry point of a program is a loop, then it may have a backedge which means the first block in the program even has a predecessor. Thus, to make things work normally, the best way is to automatically generate an `.entry` label at the beginning of the program, so that this entry block will never have a predecessor.


## Dominance Tree
To construct the dominance tree, we should first get the strict dominators and find the immediate dominators. Finding strict dominators is easy, which just needs to eliminate the node itself from the dominator set. For finding the immediate dominators, we should follow its definition -- for all the node B test its strict dominators, if some node A is not in the dominator sets of the other node that strictly dominates B, then A is the immediate dominator of B. After we get the immediate dominators, we have already got the edges for the dominator tree. Thus, I built a class `Node` for the tree representation, which stores its parents and children, and is useful for tree traversal in both directions.


## Dominance Frontier
We have the strict dominators, and constructing domination frontier is also straightforward -- "A’s dominance frontier contains B iff A does not strictly dominate B, but A does dominate some predecessor of B".

Though the implementation is easy, the result is surprising. From the [`loopcond-front`](https://github.com/sampsyo/bril/blob/main/examples/test/dom/loopcond-front.out) example, we can see that the node itself can even be contained in the dominance frontier. This may happen when a backedge/loop appears in the CFG. The entry block of the loop may dominate its predecessors from the bottom, causing it to fit the definition.


## Testings
For testing, I used a brute force method to test if some nodes are exactly the dominators of a given node. Basically, I used DFS to do the CFG traversal and generate paths from the entry point to the given node. A stack-like structure is maintained. Each time a node is visited, it will be added to the path, and at the end of an iteration, the newly added node will be popped out to restore the previous state. When the traversal reaches the destination node, this path will be added to a global path list. Finally, I test if the dominator is contained in all the paths. If so, the implementation is correct.
