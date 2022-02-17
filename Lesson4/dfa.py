import sys
import json
import argparse
from bb import form_blocks
from cfg import block_map, add_terminators, get_edges

"""
Worklist algorithm:
Given a CFG, an initial value init, and functions merge and transfer

in[entry] = init
out[*] = init

worklist = all blocks
while worklist is not empty:
    b = pick any block from worklist
    in[b] = merge(out[p] for every predecessor p of b)
    out[b] = transfer(b, in[b])
    if out[b] changed:
        worklist += successors of b
"""

def dfa(cfg, init, merge, transfer):
    """Dataflow Analysis
    """
    preds, succs = get_edges(cfg)

    in_b = {}
    out_b = {}
    # find entry block
    for b_name in preds:
        if len(preds[b_name]) == 0:
            entry = b_name
            break

    # initialization
    worklist = []
    in_b[entry] = init
    for b_name in cfg:
        if b_name != entry:
            in_b[b_name] = set() # placeholder
        out_b[b_name] = init
        worklist.append(b_name)

    # worklist algorithm
    while len(worklist) != 0:
        b_name = worklist.pop(0) # from front
        # print(b_name)
        for pred in preds[b_name]:
            in_b[b_name] = merge(in_b[b_name], out_b[pred])
        new_v = transfer(cfg[b_name], in_b[b_name])
        # print("out_v", new_v)
        if out_b[b_name] != new_v:
            for succ in succs[b_name]:
                if succ not in worklist:
                    worklist.append(succ)
            out_b[b_name] = new_v

    return in_b, out_b

def reaching_defition(func):
    cnt_def = 0
    # label instructions
    for instr in func["instrs"]:
        if "dest" in instr: # definition
            instr["id"] = "d{}_{}".format(cnt_def, instr["dest"])
            cnt_def += 1

    # function arguments are also definitions
    init_def = set()
    if "args" in func:
        for idx, arg in enumerate(func["args"]):
            def_id = "arg{}_{}".format(idx, arg["name"])
            init_def.add(def_id)

    def transfer_reaching_def(block, in_b): # work on instructions
        def_b = set()
        kill_b = set()
        for instr in block:
            if "dest" in instr:
                for def_id in in_b:
                    def_var = def_id.split("_")[-1]
                    if instr["dest"] == def_var:
                        kill_b.add(def_id)
                def_b.add(instr["id"])
        return def_b.union(in_b - kill_b)

    in_b, out_b = dfa(name2block,
                      init_def,
                      lambda x, y: x.union(y),
                      transfer_reaching_def)
    return in_b, out_b


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('-f', dest='file', default="", help='get input file')
    parser.add_argument('-reach_def', dest='reach_def', action='store_true', help='reaching definition')
    args = parser.parse_args()
    if args.file != "":
        with open(args.file, "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format

    # find top level function
    funcs = program["functions"]
    for func in funcs:
        if func["name"] == "main":
            break
    else:
        raise RuntimeError("Do not have main function")

    # construct cfg
    name2block = block_map(form_blocks(func['instrs']))
    # Insert terminators into blocks that don't have them
    add_terminators(name2block)

    if args.reach_def:
        in_b, out_b = reaching_defition(func)
        for item in zip(in_b.items(), out_b.items()):
            print("{}:".format(item[0][0]))
            print("  in: ", ", ".join(item[0][1]))
            print("  out:", ", ".join(item[1][1]))