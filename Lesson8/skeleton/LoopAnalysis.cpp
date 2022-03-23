#include "llvm/Analysis/LoopInfo.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/Scalar.h"
#include "llvm/Transforms/Utils.h"
#include "llvm/Transforms/Utils/LoopSimplify.h"
#include "llvm/IR/CFG.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

using namespace llvm;

namespace {

class InstVisitor {
public:
  void visit(Value *inst) {
    if (auto cast = dyn_cast<CastInst>(inst)) {
      visit(cast->getOperand(0));
    } else if (auto load = dyn_cast<LoadInst>(inst)) {
      this->index += std::string(load->getOperand(0)->getName());
    } else if (auto cst = dyn_cast<ConstantInt>(inst)) {
      this->index += std::to_string(cst->getSExtValue());
    } else if (auto bin = dyn_cast<BinaryOperator>(inst)) {
      auto op0 = bin->getOperand(0);
      auto op1 = bin->getOperand(1);
      visit(op0);
      if (bin->getOpcode() == Instruction::Add)
        this->index += "+";
      else if (bin->getOpcode() == Instruction::Sub)
        this->index += "-";
      else if (bin->getOpcode() == Instruction::Mul)
        this->index += "*";
      else if (bin->getOpcode() == Instruction::UDiv ||
               bin->getOpcode() == Instruction::SDiv)
        this->index += "/";
      visit(op1);
    }
  }
  std::string getIndexString() const { return index; }

private:
  std::string index = "";
};

/// Update LoopInfo, after interchanging. NewInner and NewOuter refer to the
/// new inner and outer loop after interchanging: NewInner is the original
/// outer loop and NewOuter is the original inner loop.
///
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

  // get loop body
  // BasicBlock *getLoopBody(BasicBlock *bb) {
  //   for (BasicBlock* succ : successors(bb)) {
  //     return succ;
  //   }
  // }

  virtual bool runOnFunction(Function &F) {
    // llvm/Analysis/LoopInfo.h
    auto &LI = getAnalysis<LoopInfoWrapperPass>().getLoopInfo();
    int cnt = 0;
    Loop* OuterLoop = nullptr;
    Loop* InnerLoop = nullptr;
    int OuterLoopIdx = 1;
    int InnerLoopIdx = 2;
    // llvm/Analysis/LoopInfo.h
    for (Loop *L : LI.getLoopsInPreorder()) {
      llvm::errs() << L->getHeader()->getName() << "\n";
      if (OuterLoopIdx == cnt) {
        llvm::errs() << "Outer Loop: " << L->getName() << "\n";
        OuterLoop = L;
      } else if (InnerLoopIdx == cnt) {
        llvm::errs() << "Inner Loop: " << L->getName() << "\n";
        InnerLoop = L;
      }
      cnt++;
    }
    // https://llvm.org/doxygen/classllvm_1_1BasicBlock.html
    llvm::errs() << "\n";
    BasicBlock *InnerLoopPreheader = InnerLoop->getLoopPreheader();
    BasicBlock *OuterLoopPreheader = OuterLoop->getLoopPreheader();
    BasicBlock *InnerLoopHeader = InnerLoop->getHeader();
    BasicBlock *OuterLoopHeader = OuterLoop->getHeader();
    BasicBlock *InnerLoopLatch = InnerLoop->getLoopLatch();
    BasicBlock *OuterLoopLatch = OuterLoop->getLoopLatch();
    BasicBlock *InnerLoopExit = InnerLoop->getExitBlock();
    BasicBlock *OuterLoopExit = OuterLoop->getExitBlock();
    BasicBlock *InnerLoopBody = InnerLoopHeader->getNextNode();
    InnerLoopLatch->dump();
    InnerLoopExit->dump();
    // move headers
    InnerLoopHeader->moveBefore(OuterLoopHeader);
    OuterLoopHeader->moveBefore(InnerLoopBody);
    // move preheaders
    InnerLoopPreheader->moveBefore(InnerLoopHeader);
    OuterLoopPreheader->moveBefore(OuterLoopHeader);
    // move exits
    BasicBlock *OuterLoopExitNext = OuterLoopExit->getNextNode();
    InnerLoopExit->moveBefore(OuterLoopExitNext);
    InnerLoopLatch->moveBefore(InnerLoopExit);
    OuterLoopExit->moveBefore(InnerLoopLatch);
    OuterLoopLatch->moveBefore(OuterLoopExit);
    F.dump();

    // update branch op
    // for (Use &Op : BI->operands())
    //   if (Op == OldBB) {
    //     Op.set(NewBB);
    //     Changed = true;
    //   }
    return true;
  }

  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.addRequired<LoopInfoWrapperPass>();
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