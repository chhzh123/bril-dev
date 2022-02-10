import sys
import json

def find_val(table, val):
    idx = -1
    for i, item in enumerate(table):
        if item[0] == val:
            return i
    return idx

def lvn(prg):
    """Local Variable Numbering (LVN)
    """
    funcs = prg["functions"]

    # first find the top-level function
    # and record the function map
    func_map = {}
    for func in funcs:
        func_map[func["name"]] = func
    top_func = func_map["main"]

    def runOnFunction(func):
        # lvn_table: mapping from value tuples to canonical variables, with each row numbered
        lvn_table = []
        # (val, var)
        # val: (op, ref[arg[0]], ref[arg[1]], ...)
        # type needs not be considered since op has already determined the type
        var2index = {} # variable -> lvn index

        for i, instr in enumerate(func["instrs"]):
            # print(i, instr)
            if "op" in instr:
                # construct value
                value = [instr["op"]]
                if instr["op"] == "const":
                    value.append(instr["value"])
                else: # suppose instr has args
                    for arg in instr["args"]:
                        value.append(var2index[arg]) # should be already defined
                value = tuple(value)
                # print("value", value)

                # check if the value is in the table
                idx = find_val(lvn_table, value)
                if idx != -1:
                    # print("computed before")
                    # the value has been computed before; reuse it
                    num, var = idx, lvn_table[idx][1]
                    # replace instr with copy of var
                    instr["op"] = "id"
                    instr["args"] = [var]
                else:
                    # A newly computed value
                    num = len(lvn_table)
                    if "dest" in instr:
                        dest = instr["dest"]
                        # if instr will be overwritten later
                        written_flag = False
                        for latter_instr in func["instrs"][i+1:]:
                            if "dest" in latter_instr and dest == latter_instr["dest"]:
                                written_flag = True
                                break
                        if written_flag:
                            dest += "_new" # fresh variable name
                            instr["dest"] = dest
                        else:
                            pass
                        lvn_table.append((value, dest))

                        # replace a with table[var2num[a]].var
                        if "args" in instr:
                            for arg_idx in range(len(instr["args"])):
                                instr["args"][arg_idx] = lvn_table[var2index[instr["args"][arg_idx]]][1]
                            # print("new", instr["args"])

                if "dest" in instr:
                    var2index[instr["dest"]] = num
                # print(var2index)

    for func in funcs:
        runOnFunction(func)
    return prg

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format
    new_program = lvn(program)
    print(json.dumps(new_program, indent=2))