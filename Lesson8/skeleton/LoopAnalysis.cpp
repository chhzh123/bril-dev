#include "llvm/Analysis/LoopInfo.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/CFG.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
#include "llvm/Transforms/Scalar.h"
#include "llvm/Transforms/Utils.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include "llvm/Transforms/Utils/LoopSimplify.h"

using namespace llvm;

namespace {

/// Before interchanging, we have the following structure
/// Outer preheader
//  Outer header
//    Inner preheader
//    Inner header
//      Inner body
//      Inner latch
//   outer bbs
//   Outer latch
//
// After interchanging:
// Inner preheader
// Inner header
//   Outer preheader
//   Outer header
//     Inner body
//     outer bbs
//     Outer latch
//   Inner latch
struct LoopAnalysisPass : public FunctionPass {
  static char ID;
  LoopAnalysisPass() : FunctionPass(ID) {}

  // update branch operand
  void updateBranchOperand(BranchInst *BI, BasicBlock *OldBB,
                           BasicBlock *NewBB) {
    for (Use &Op : BI->operands())
      if (Op == OldBB) {
        Op.set(NewBB);
      }
  }

  void reorder(Function &F, int OuterLoopIdx, int InnerLoopIdx) {
    // llvm/Analysis/LoopInfo.h
    auto *LI = &getAnalysis<LoopInfoWrapperPass>().getLoopInfo();
    auto *DT = &getAnalysis<DominatorTreeWrapperPass>().getDomTree();
    int cnt = 0;
    Loop *OuterLoop = nullptr;
    Loop *InnerLoop = nullptr;
    // llvm/Analysis/LoopInfo.h
    for (Loop *L : LI->getLoopsInPreorder()) {
      if (OuterLoopIdx == cnt) {
        OuterLoop = L;
      } else if (InnerLoopIdx == cnt) {
        InnerLoop = L;
      }
      cnt++;
    }
    // https://llvm.org/doxygen/classllvm_1_1BasicBlock.html
    BasicBlock *InnerLoopPreheader = InnerLoop->getLoopPreheader();
    BasicBlock *OuterLoopPreheader = OuterLoop->getLoopPreheader();
    if (OuterLoopPreheader->isEntryBlock())
      OuterLoopPreheader = SplitBlock(
          OuterLoopPreheader, OuterLoopPreheader->getTerminator(), DT, LI);
    BasicBlock *InnerLoopHeader = InnerLoop->getHeader();
    BasicBlock *OuterLoopHeader = OuterLoop->getHeader();
    BasicBlock *InnerLoopLatch = InnerLoop->getLoopLatch();
    BasicBlock *OuterLoopLatch = OuterLoop->getLoopLatch();
    BasicBlock *InnerLoopExit = InnerLoop->getExitBlock();
    BasicBlock *OuterLoopExit = OuterLoop->getExitBlock();
    BasicBlock *InnerLoopSuccessor = InnerLoopHeader->getNextNode();
    BasicBlock *OuterLoopPredecessor =
        OuterLoopPreheader->getUniquePredecessor();
    BasicBlock *InnerLoopLatchPredecessor =
        InnerLoopLatch->getUniquePredecessor();
    BasicBlock *OuterLoopExitSuccessor = OuterLoopExit->getNextNode();

    // move headers
    InnerLoopHeader->moveBefore(OuterLoopHeader);
    OuterLoopHeader->moveBefore(InnerLoopSuccessor);
    // move preheaders
    InnerLoopPreheader->moveBefore(InnerLoopHeader);
    OuterLoopPreheader->moveBefore(OuterLoopHeader);
    // move exits
    BasicBlock *OuterLoopExitNext = OuterLoopExit->getNextNode();
    InnerLoopExit->moveBefore(OuterLoopExitNext);
    InnerLoopLatch->moveBefore(InnerLoopExit);
    OuterLoopExit->moveBefore(InnerLoopLatch);
    OuterLoopLatch->moveBefore(OuterLoopExit);

    // Update branch instructions
    BranchInst *OuterLoopHeaderBI =
        dyn_cast<BranchInst>(OuterLoopHeader->getTerminator());
    BranchInst *InnerLoopHeaderBI =
        dyn_cast<BranchInst>(InnerLoopHeader->getTerminator());
    BranchInst *OuterLoopLatchBI =
        dyn_cast<BranchInst>(OuterLoopLatch->getTerminator());
    BranchInst *InnerLoopLatchBI =
        dyn_cast<BranchInst>(InnerLoopLatch->getTerminator());
    BranchInst *InnerLoopExitBI =
        dyn_cast<BranchInst>(InnerLoopExit->getTerminator());
    BranchInst *OuterLoopExitBI =
        dyn_cast<BranchInst>(OuterLoopExit->getTerminator());
    BranchInst *OuterLoopPredecessorBI =
        dyn_cast<BranchInst>(OuterLoopPredecessor->getTerminator());
    updateBranchOperand(OuterLoopPredecessorBI, OuterLoopHeader,
                        InnerLoopPreheader);
    updateBranchOperand(OuterLoopHeaderBI, InnerLoopPreheader,
                        InnerLoopSuccessor);
    updateBranchOperand(InnerLoopHeaderBI, InnerLoopSuccessor,
                        OuterLoopPreheader);
    updateBranchOperand(InnerLoopExitBI, OuterLoopLatch,
                        OuterLoopExitSuccessor);
    updateBranchOperand(OuterLoopExitBI, OuterLoopExitSuccessor,
                        InnerLoopLatch);
  }

  virtual bool runOnFunction(Function &F) {
    reorder(F, 1, 2);
    // reorder(F, 2, 3);
    // reorder(F, 1, 3);
    F.dump();
    return true;
  }

  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.addRequired<LoopInfoWrapperPass>();
    AU.addRequired<DominatorTreeWrapperPass>();
    AU.addPreserved<LoopInfoWrapperPass>();
  }
};
} // namespace

char LoopAnalysisPass::ID = 0;

static RegisterPass<LoopAnalysisPass>
    X("loop-analysis", "LoopAnalysis Pass",
      false /* Only looks at CFG (read-only) */,
      false /* Analysis Pass (write) */);

static RegisterStandardPasses Y(PassManagerBuilder::EP_EarlyAsPossible,
                                [](const PassManagerBuilder &Builder,
                                   legacy::PassManagerBase &PM) {
                                  PM.add(new LoopAnalysisPass());
                                });