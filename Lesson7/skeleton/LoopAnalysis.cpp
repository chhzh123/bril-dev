#include "llvm/Analysis/LoopInfo.h"
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

struct LoopAnalysisPass : public FunctionPass {
  static char ID;
  LoopAnalysisPass() : FunctionPass(ID) {}

  virtual bool runOnFunction(Function &F) {
    // llvm/Analysis/LoopInfo.h
    auto &LI = getAnalysis<LoopInfoWrapperPass>().getLoopInfo();
    int cnt = 0;
    for (Loop *L : LI) {
      errs() << "\nLoop " << cnt++ << ":\n";
      for (auto bb = L->block_begin(), be = L->block_end(); bb != be; ++bb) {
        for (BasicBlock::iterator instr = (*bb)->begin(), ee = (*bb)->end(); instr != ee; ++instr) {
          // https://llvm.org/doxygen/classllvm_1_1Instruction.html
          // ref: llvm/lib/Transforms/Scalar/LoopFlatten.cpp
          if (auto *GEP = dyn_cast<GetElementPtrInst>(instr)) {
            for (Value *GEPUser : instr->users()) {
              auto *GEPUserInst = cast<Instruction>(GEPUser);
              if (isa<LoadInst>(GEPUserInst) || isa<StoreInst>(GEPUserInst)) {
                if (isa<LoadInst>(GEPUserInst)) {
                  errs() << "Load: ";
                } else if (isa<StoreInst>(GEPUserInst)) {
                  errs() << "Store: ";
                }
                GEPUserInst->dump();
                // print original array
                errs() << "Original: ";
                errs() << GEP->getPointerOperand()->getName() << "[";
                for (auto i = GEP->idx_begin(), e = GEP->idx_end(); i != e;
                     ++i) {
                  if (i == GEP->idx_begin())
                    continue;
                  InstVisitor visitor;
                  visitor.visit(i->get());
                  std::string str = visitor.getIndexString();
                  errs() << str;
                }
                errs() << "]\n";
              }
            }
          }
        }
      }
    }
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