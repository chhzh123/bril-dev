# Lesson 8 - Loop Optimization

* First, pick Bril or LLVM as your starting point.
    * You can work in the SSA form of Bril if you want.
    * If you pick Bril, you’ll need to find the natural loops yourself. If you pick LLVM, you can use a LoopPass to skip that step, but of course other parts of the implementation will be trickier.
* Then, pick your optimization. You can either:
    * Choose one of the loop-based optimizations mentioned above in this lesson. (Including one of the ones I just mentioned at the end without describing in detail.) (If you’re having trouble deciding, I recommend LICM.)
    * Propose your own. (DM me on Zulip before you start working on it to clear your idea.)
* Implement your optimization.
    * Rigorously evaluate its performance impact. See the SIGPLAN empirical evaluation guidelines for the definition of “rigorous.”
    * In Bril, you can use the Bril benchmarks.
    * If you choose LLVM, select an existing (small!) benchmark suite such as Embench. Please violate the SIGPLAN guideline about using complete benchmark suites, an cherry-pick a convenient subset, to make this evaluation tractable.