import sys
import json

def dce(prg):
    """Dead Code Elimination (DCE)
    """
    funcs = prg["functions"]

    # first find the top-level function
    # and record the function map
    func_map = {}
    for func in funcs:
        func_map[func["name"]] = func
    top_func = func_map["main"]

    def runOnFunction(func):
        # find the used list
        used = set()
        for instr in func["instrs"]:
            if "args" in instr:
                for arg in instr["args"]:
                    used.add(arg)
        # traverse again to check whether those args are used
        new_instrs = []
        for instr in func["instrs"]:
            if "dest" in instr and instr["dest"] not in used:
                pass
            else:
                new_instrs.append(instr)
        func["instrs"] = new_instrs

    runOnFunction(top_func)
    return prg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format
    new_program = dce(program)
    print(json.dumps(new_program, indent=2))