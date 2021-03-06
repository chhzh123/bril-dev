import sys
import json
from bb import form_blocks

def find_block(blocks, label):
    for block in blocks:
        if "label" in block[0] and block[0]["label"] == label:
            return block
    return None

def dce(prg):
    """Dead Code Elimination (DCE)
    """
    funcs = prg["functions"]

    # first find the top-level function
    # and record the function map
    func_map = {}
    for func in funcs:
        func_map[func["name"]] = func

    def runOnBlock(block_instrs):
        while True:
            prev_size = len(block_instrs)
            # find the used list
            used = set()
            for instr in block_instrs:
                if "args" in instr:
                    for arg in instr["args"]:
                        used.add(arg)
            # traverse again to check whether those args are used
            new_instrs = []
            for instr in block_instrs:
                if "dest" in instr and instr["dest"] not in used:
                    pass
                else:
                    new_instrs.append(instr)
            block_instrs = new_instrs.copy()
            # reassignment
            last_def = {} # var->instr
            for instr in block_instrs:
                # check for uses
                if "args" in instr:
                    for arg in instr["args"]:
                        last_def.pop(arg, None)
                # check for defs
                if "dest" in instr:
                    if instr["dest"] in last_def:
                        new_instrs.remove(last_def[instr["dest"]])
                    last_def[instr["dest"]] = instr
            block_instrs = new_instrs.copy()
            curr_size = len(block_instrs)
            if prev_size == curr_size:
                break
        return block_instrs

    for func in funcs:
        blocks = []
        for block in form_blocks(func["instrs"]):
            blocks.append(block)
        new_instrs = []
        # traverse the CFG according to control flow
        block = blocks[0]
        while True:
            new_instrs += block
            if block[-1]["op"] == "jmp":
                label = block[-1]["labels"][0]
                block = find_block(blocks, label)
                if block == None:
                    break
            else:
                break
        func["instrs"] = runOnBlock(new_instrs)
    return prg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format
    new_program = dce(program)
    print(json.dumps(new_program, indent=2))