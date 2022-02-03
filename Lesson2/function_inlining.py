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
    fid = -1
    for instr in top_func["instrs"]:
        # label does not have "op" key
        if "op" in instr and instr["op"] == "call":
            call_op = instr
            # find the callee function
            callee = func_map[instr["funcs"][0]] # * not sure why here is func's'
            fid += 1

            # construct local var in function -> global var mapping
            if "args" in instr:
                global_vars = instr["args"]
                callee_args_map = {arg["name"]: global_vars[idx] for idx, arg in enumerate(callee["args"])}
            else:
                callee_args_map = {}
            # also add return value's mapping
            callee_ret_map = {}
            if "dest" in call_op:
                # traverse all the instructions in callee and find return op
                for instr in callee["instrs"]:
                    if "op" in instr and instr["op"] == "ret":
                        callee_ret_map[instr["args"][0]] = call_op["dest"] # * not sure why enable multiple returns

            # replace all the arguments to global variable
            for callee_instr in callee["instrs"]:
                # prevent nested function call
                if "op" in callee_instr and callee_instr["op"] == "call":
                    raise RuntimeError("Not support nested function call!")
                # check operands (inputs)
                if "args" in callee_instr:
                    new_args = []
                    for arg in callee_instr["args"]:
                        if arg in callee_args_map:
                            new_args.append(callee_args_map[arg])
                        elif arg in callee_ret_map:
                            new_args.append(callee_ret_map[arg])
                        else:
                            new_args.append(arg)
                    # reset operands
                    callee_instr["args"] = new_args
                # check returns (outputs)
                if "dest" in callee_instr:
                    dest = callee_instr["dest"]
                    if dest in callee_ret_map:
                        callee_instr["dest"] = callee_ret_map[dest]
                    else:
                        # avoid function naming conflict
                        original_name = callee_instr["dest"]
                        callee_instr["dest"] = callee_instr["dest"] + "_fvar{}".format(fid)
                        callee_args_map[original_name] = callee_instr["dest"]
                # rename possible conflicting scopes
                if "label" in callee_instr:
                    callee_instr["label"] = callee_instr["label"] + "_flabel{}".format(fid)
                if "labels" in callee_instr:
                    new_labels = []
                    for label in callee_instr["labels"]:
                        new_labels.append(label + "_flabel{}".format(fid))
                    callee_instr["labels"] = new_labels
                # no need to add return function
                if "op" in callee_instr and callee_instr["op"] == "ret":
                    pass
                else:
                    new_instrs.append(callee_instr)
            # after replace do nesting
        else:
            new_instrs.append(instr)
    # create new main function
    new_prg = {}
    new_main = {}
    new_main["name"] = "main"
    if "args" in func_map["main"]:
        new_main["args"] = func_map["main"]["args"]
    new_main["instrs"] = new_instrs
    new_prg["functions"] = [new_main]
    return new_prg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format
    new_program = inline_function(program)
    print(json.dumps(new_program, indent=2))