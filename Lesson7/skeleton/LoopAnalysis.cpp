#include "llvm/Analysis/LoopAccessAnalysis.h"
#include "llvm/Analysis/LoopAnalysisManager.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Transforms/Scalar.h"
#include "llvm/Transforms/Utils.h"
#include "llvm/Transforms/Utils/LoopSimplify.h"

#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

using namespace llvm;

namespace {
struct LoopAnalysisPass : public FunctionPass {
  static char ID;
  LoopAnalysisPass() : FunctionPass(ID) {}

  virtual bool runOnFunction(Function &F) {
    errs() << "I saw a function called " << F.getName() << "!\n";
    for (Function::iterator bb = F.begin(), e = F.end(); bb != e; ++bb) {
      for (BasicBlock::iterator instr = bb->begin(), e = bb->end(); instr != e;
           ++instr) {
        // https://llvm.org/doxygen/classllvm_1_1Instruction.html
        // ref: llvm/lib/Transforms/Scalar/LoopFlatten.cpp
        if (auto *GEP = dyn_cast<GetElementPtrInst>(instr)) {
          errs() << "Indices:" << GEP->getNumIndices() << "\n";
          GEP->getPointerOperand()->dump();
          errs() << GEP->getPointerOperand()->getName() << "\n";
          for (auto i = GEP->idx_begin(), e = GEP->idx_end(); i != e; ++i) {
            if (i == GEP->idx_begin())
              continue;
            // https://llvm.org/doxygen/classllvm_1_1Value.html
            // Value* idx = i->get();
            auto idx_inst = cast<Instruction>(i);
            if (auto cast = dyn_cast<CastInst>(idx_inst)) {
              errs() << "cast\n";
              Value* op = cast->getOperand(0);
              if (auto load = dyn_cast<LoadInst>(op)) {
                errs() << load->getOperand(0)->getName() << "\n";
              }
            }
            // idx_inst->dump();
          }
          for (Value *GEPUser : instr->users()) {
            auto *GEPUserInst = cast<Instruction>(GEPUser);
            if (isa<LoadInst>(GEPUserInst) || isa<StoreInst>(GEPUserInst))
              GEPUserInst->dump();
          }
        }
      }
    }
    // llvm/Analysis/LoopInfo.h
    auto &LI = getAnalysis<LoopInfoWrapperPass>().getLoopInfo();
    auto &LAA = getAnalysis<LoopAccessLegacyAnalysis>();
    for (Loop *L : LI) {
      L->dumpVerbose();
      errs() << "\n";
      const LoopAccessInfo &LA = LAA.getInfo(L);
      llvm::raw_ostream &output = llvm::outs();
      LA.print(output);
      ScalarEvolution &SE = getAnalysis<ScalarEvolutionWrapperPass>().getSE();
      auto iv = L->getInductionVariable(SE);
      assert(iv == NULL);
      errs() << "# Loads:" << LA.getNumLoads() << "\n";
      errs() << "# Stores:" << LA.getNumStores() << "\n";
      // LAA.getInstructionsForAccess()
    }
    return false;
  }

  void getAnalysisUsage(AnalysisUsage &AU) const override {
    AU.addRequired<LoopInfoWrapperPass>();
    AU.addPreserved<LoopInfoWrapperPass>();
    AU.addRequired<LoopAccessLegacyAnalysis>();
    AU.addRequired<ScalarEvolutionWrapperPass>();
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