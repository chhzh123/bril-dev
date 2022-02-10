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
        while True: # iterate till program is not changed (used for constant propagation)
            is_prg_changed = False
            conflict_id = 0
            # lvn_table: mapping from value tuples to canonical variables, with each row numbered
            lvn_table = []
            # (val, var)
            # val: (op, ref[arg[0]], ref[arg[1]], ...)
            # type needs not be considered since op has already determined the type
            var2index = {} # variable -> lvn index

            # append function arguments
            if "args" in func:
                for arg in func["args"]:
                    arg = arg["name"]
                    lvn_table.append((("args"), arg))
                    var2index[arg] = len(lvn_table) - 1

            for i, instr in enumerate(func["instrs"]):
                if "op" in instr:
                    # construct value
                    if instr["op"] == "id":
                        value = lvn_table[var2index[instr["args"][0]]][0]
                    else:
                        value = []
                        if instr["op"] == "const":
                            value.append(instr["value"])
                        else: # suppose instr has args
                            if "args" not in instr: # jmp
                                continue
                            for arg in instr["args"]:
                                value.append(var2index[arg]) # should be already defined
                            # commutivity -> canonicalize
                            if instr["op"] in ["add", "mul"]:
                                value.sort()
                        value = tuple([instr["op"]] + value)

                    # check if the value is in the table
                    idx = find_val(lvn_table, value)
                    if idx != -1:
                        # the value has been computed before; reuse it
                        num, var = idx, lvn_table[idx][1]
                        if instr["op"] == "id": # copy propagation
                            # if the copied variable is a constant
                            instr["op"] = value[0]
                            instr["value"] = value[1]
                        else: # replace instr with copy of var
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
                                original_dest = dest
                                dest += "_new{}".format(conflict_id) # fresh variable name
                                conflict_id += 1
                                instr["dest"] = dest
                                # update the latter references
                                for latter_instr in func["instrs"][i+1:]:
                                    if "args" in latter_instr:
                                        for arg_idx in range(len(latter_instr["args"])):
                                            if original_dest == latter_instr["args"][arg_idx]:
                                                latter_instr["args"][arg_idx] = dest
                                    if "dest" in latter_instr and original_dest == latter_instr["dest"]:
                                        # only instructions in between should be modified
                                        break
                            else:
                                pass
                            lvn_table.append((value, dest))

                        # replace a with table[var2num[a]].var
                        if "args" in instr:
                            for arg_idx in range(len(instr["args"])):
                                instr["args"][arg_idx] = lvn_table[var2index[instr["args"][arg_idx]]][1]
                        
                            # constant folding
                            constants = []
                            all_variables = []
                            for arg in instr["args"]:
                                item = lvn_table[var2index[arg]]
                                if item[0][0] == "const":
                                    # get actual values
                                    constants.append(lvn_table[var2index[item[1]]][0][1])
                                all_variables.append(lvn_table[var2index[item[1]]][1])
                            all_same = True
                            first_var = all_variables[0]
                            for var in all_variables[1:]:
                                if var != first_var:
                                    all_same = False
                                    break
                            # all operands are the same
                            op = instr["op"]
                            result = None
                            if all_same:
                                if op == "ne":
                                    result = False
                                elif op == "eq":
                                    result = True
                                elif op == "le":
                                    result = True
                                elif op == "lt":
                                    result = False
                                elif op == "gt":
                                    result = False
                                elif op == "ge":
                                    result = True
                            if len(constants) > 0:
                                if op == "and":
                                    if constants[0] == False:
                                        result = False
                                elif op == "or":
                                    if constants[0] == True:
                                        result = True
                            # all operands are constants
                            if len(constants) == 2 and len(constants) == len(instr["args"]):
                                if op == "ne":
                                    result = (constants[0] != constants[1])
                                elif op == "eq":
                                    result = (constants[0] == constants[1])
                                elif op == "le":
                                    result = (constants[0] <= constants[1])
                                elif op == "lt":
                                    result = (constants[0] < constants[1])
                                elif op == "gt":
                                    result = (constants[0] > constants[1])
                                elif op == "ge":
                                    result = (constants[0] >= constants[1])
                                elif op == "and":
                                    result = (constants[0] and constants[1])
                                elif op == "or":
                                    result = (constants[0] or constants[1])
                                elif op == "not":
                                    result = not (constants[0])
                                elif op == "add":
                                    result = (constants[0] + constants[1])
                                elif op == "sub":
                                    result = (constants[0] - constants[1])
                                elif op == "mul":
                                    result = (constants[0] * constants[1])
                                elif op == "div":
                                    if constants[1] != 0: # avoid divided by 0
                                        result = (constants[0] / constants[1])
                            # change operation
                            if result != None:
                                is_prg_changed = True
                                instr["op"] = "const"
                                instr["value"] = result
                                instr.pop("args", None)

                    if "dest" in instr:
                        var2index[instr["dest"]] = num

            if not is_prg_changed:
                break

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