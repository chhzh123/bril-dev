#include "llvm/IR/Function.h"
#include "llvm/Pass.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/Instructions.h"

#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"

using namespace llvm;

namespace {
struct SkeletonPass : public FunctionPass {
  static char ID;
  SkeletonPass() : FunctionPass(ID) {}

  virtual bool runOnFunction(Function &F) {
    errs() << "I saw a function called " << F.getName() << "!\n";
    for (Function::iterator bb = F.begin(), e = F.end(); bb != e; ++bb) {
      for (BasicBlock::iterator instr = bb->begin(), e = bb->end(); instr != e; ++instr) {
        // https://llvm.org/doxygen/classllvm_1_1Instruction.html
        // ref: llvm/lib/Transforms/Scalar/LoopFlatten.cpp
        if (auto *GEP = dyn_cast<GetElementPtrInst>(instr)) {
          for (Value *GEPUser : instr->users()) {
            auto *GEPUserInst = cast<Instruction>(GEPUser);
            if (isa<LoadInst>(GEPUserInst) || isa<StoreInst>(GEPUserInst))
              GEPUserInst->dump();
          }
        }
      }
    }
    return false;
  }
};
} // namespace

char SkeletonPass::ID = 0;

static RegisterPass<SkeletonPass> X("skeleton", "Skeleton Pass",
                                    false /* Only looks at CFG (read-only) */,
                                    false /* Analysis Pass (write) */);

static RegisterStandardPasses Y(PassManagerBuilder::EP_EarlyAsPossible,
                                [](const PassManagerBuilder &Builder,
                                   legacy::PassManagerBase &PM) {
                                  PM.add(new SkeletonPass());
                                });