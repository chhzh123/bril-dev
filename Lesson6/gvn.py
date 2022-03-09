import sys
import json
import argparse
from utils.bb import form_blocks
from utils.cfg import block_map, add_terminators, get_edges
from utils.dom import dominance, domination_frontier, imm_dominance, dominator_tree

# gvn_table (hash table): mapping from value tuples to canonical variables, with each row numbered
gvn_table = []
# (val, var)
# val: (op, ref[arg[0]], ref[arg[1]], ...)
# type needs not be considered since op has already determined the type
var2index = {} # variable -> gvn index (VN)

def find_val(table, instr):
    val = [instr["op"]]
    for arg in instr["args"]:
        val.append(arg)
    val = tuple(val)
    for i, item in enumerate(table):
        if item[0] == val:
            return item[1]
    return None

def insert_var(table, instr):
    val = [instr["op"]]
    if "args" in instr:
        for arg in instr["args"]:
            val.append(var2index[arg])
    else:
        val.append(instr["value"])
    table.append((tuple(val), instr["dest"]))

def print_instr(instr):
    if "op" in instr:
        if "args" in instr:
            print(instr["op"] + " " + ",".join(instr["args"]))
        elif instr["op"] in ["const", "br"]:
            print(instr["op"] + " " + str(instr["value"]))
        else: # jmp
            print(instr["op"] + " " + instr["labels"][0])
    else:
        print(instr["label"])

def dvnt(block_name):
    """
    Dominator-based value numbering technique
    https://www.cs.tufts.edu/~nr/cs257/archive/keith-cooper/value-numbering.pdf
    """
    block = cfg[block_name]
    for instr in block:
        if "op" in instr and instr["op"] == "phi":
            # if p is meaningless or redundant
            if instr["args"][0] == instr["args"][1]: # meaningless
                instr.pop("labels")
                instr["op"] = "id"
                instr["args"] = [instr["args"][0]]
                # Put the value number for p into VN[n]
                var2index[instr["dest"]] = var2index[instr["args"][0]]
                # Remove p
            else:
                var = find_val(gvn_table, instr)
                if var != None: # redundant
                    instr.pop("labels")
                    instr["op"] = "id"
                    instr["args"] = [var]
                    var2index[instr["dest"]] = var2index[var]
                else:
                    # VN[n] ← n
                    var2index[instr["dest"]] = instr["dest"]
                    # Add p to the hash table
                    insert_var(gvn_table, instr)
    for instr in block:
        # for each assignment a of the form “x ← y op z” in B
        if "dest" in instr and instr["op"] not in ["id", "const", "phi"]:
            # Overwrite y with VN[y] and z with VN[z]
            y, z = instr["args"]
            instr["args"] = [var2index[y], var2index[z]]
            # expr ← <y op z>
            var = find_val(gvn_table, instr)
            # if expr can be simplified to expr'
                # Replace a with “x ← expr'”
                # expr ← expr0
            # if expr is found in the hash table with value number v
            if var != None:
                # VN[x] ← v
                var2index[instr["dest"]] = var
                # Remove a
                instr["op"] = "id"
                instr["args"] = [var]
            else:
                # VN[x] ← x
                var2index[instr["dest"]] = instr["dest"]
                # Add expr to the hash table with value number x
                insert_var(gvn_table, instr)
    # for each successor s of B
    for succ_name in succs[block_name]:
        # Adjust the φ-function inputs in s
        for instr in cfg[succ_name]:
            if "op" in instr and instr["op"] == "phi":
                for idx, label in enumerate(instr["labels"]):
                    if label == block_name:
                        instr["args"][idx] = var2index[instr["args"][idx]]
    # for each child c of B in the dominator tree
    for child in name2node[block_name].children:
        dvnt(child.name)
    # Clean up the hash table after leaving this scope


def global_value_numbering(cfg):

    dvnt("B1")

    # get back results
    instrs = []
    flag = False
    for block_name in cfg:
        for instr in cfg[block_name]:
            if ("arg" in instr and "myentry" in instr["args"]) or ("labels" in instr and "myentry" in instr["labels"]):
                flag = True
    for block_name in cfg:
        if block_name == "myentry" and not flag:
            continue
        instrs.append({"label": block_name})
        for instr in cfg[block_name]:
            if "op" in instr and instr["op"] == "phi_": # fix phi_
                instr["op"] = "phi"
            if instr["op"] != "id": # remove instructions
                instrs.append(instr)
    return instrs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('-f', dest='file', default="", help='get input file')
    args = parser.parse_args()
    if args.file != "":
        with open(args.file, "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format

    # find top level function
    funcs = program["functions"]
    for func in funcs:
        # construct cfg: name -> block
        entry = [{"label": "myentry"}]
        if "op" in func["instrs"][0]: # no label for the entry block
            entry += [{"label": "b1"}]
        func['instrs'] = entry + func['instrs']
        cfg = block_map(form_blocks(func['instrs']))
        # Insert terminators into blocks that don't have them
        add_terminators(cfg)

        preds, succs = get_edges(cfg)

        dom = dominance(cfg, func, preds)
        frontiers = domination_frontier(dom, preds)
        idom = imm_dominance(dom)

        name2node = dominator_tree(dom, preds)
        # print("Dominator tree")
        # for name in name2node:
        #     print(" ", name, name2node[name].children)
        # print()

        # append function arguments
        if "args" in func:
            for arg in func["args"]:
                arg = arg["name"]
                gvn_table.append((("args"), arg))
                var2index[arg] = arg

        func["instrs"] = global_value_numbering(cfg)

    print(json.dumps(program, indent=2))
