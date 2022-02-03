import sys
import json

def inline_function(prg):
    """Inline all the function call for the input program
    """
    funcs = prg["functions"]

    # first find the top-level function
    # and record the function map
    func_map = {}
    for func in funcs:
        func_map[func["name"]] = func
    top_func = func_map["main"]
    # traverse the function one by one and see if there is function call
    # should work recursively
    new_instrs = []
    for instr in top_func["instrs"]:
        if instr["op"] == "call":
            call_op = instr
            # find the callee function
            callee = func_map[instr["funcs"][0]] # * not sure why here is func's'

            # construct local var in function -> global var mapping
            global_vars = instr["args"]
            callee_args_map = {arg["name"]: global_vars[idx] for idx, arg in enumerate(callee["args"])}
            # also add return value's mapping
            if "dest" in call_op:
                # traverse all the instructions in callee and find return op
                for instr in callee["instrs"]:
                    if instr["op"] == "ret":
                        callee_args_map[instr["args"][0]] = call_op["dest"] # * not sure why enable multiple returns

            # replace all the arguments to global variable
            for callee_instr in callee["instrs"]:
                # check operands
                if "args" in callee_instr:
                    new_args = []
                    for arg in callee_instr["args"]:
                        if arg in callee_args_map:
                            new_args.append(callee_args_map[arg])
                        else:
                            new_args.append(arg)
                    # reset operands
                    callee_instr["args"] = new_args
                # check returns
                if "dest" in callee_instr:
                    dest = callee_instr["dest"]
                    if dest in callee_args_map:
                        callee_instr["dest"] = callee_args_map[dest]
                # no need to add return function
                if callee_instr["op"] == "ret":
                    pass
                else:
                    new_instrs.append(callee_instr)
            # after replace do nesting
            # rename possible conflicting scopes
        else:
            new_instrs.append(instr)
    # create new main function
    new_prg = {}
    new_main = {}
    new_main["name"] = "main"
    new_main["args"] = func_map["main"]["args"]
    new_main["instrs"] = new_instrs
    new_prg["functions"] = [new_main]
    return new_prg

if __name__ == "__main__":
    with open(sys.argv[1], "r") as infile:
        program = json.load(infile)
    new_program = inline_function(program)
    print(json.dumps(new_program, indent=2))