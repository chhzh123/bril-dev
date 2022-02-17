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

def dfa(cfg, init, merge, transfer, forward=True):
    """Dataflow Analysis
    """
    preds, succs = get_edges(cfg)

    in_b = {}
    out_b = {}
    # find entry block
    for b_name in preds:
        if forward and len(preds[b_name]) == 0:
            entry = b_name
            break
        elif not forward and len(succs[b_name]) == 0:
            entry = b_name

    # initialization
    worklist = []
    if forward:
        in_b[entry] = init
    else:
        out_b[entry] = init
    for b_name in cfg:
        if b_name != entry:
            if forward:
                in_b[b_name] = set() # placeholder
            else:
                out_b[b_name] = set()
        if forward:
            out_b[b_name] = init
        else:
            in_b[b_name] = init
        worklist.append(b_name)

    if not forward:
        worklist.reverse()

    # worklist algorithm
    while len(worklist) != 0:
        b_name = worklist.pop(0) # from front
        if forward:
            for pred in preds[b_name]:
                in_b[b_name] = merge(in_b[b_name], out_b[pred])
            new_v = transfer(cfg[b_name], in_b[b_name])
            if out_b[b_name] != new_v:
                for succ in succs[b_name]:
                    if succ not in worklist:
                        worklist.append(succ)
                out_b[b_name] = new_v
        else:
            for succ in succs[b_name]:
                out_b[b_name] = merge(out_b[b_name], in_b[succ])
            new_v = transfer(cfg[b_name], out_b[b_name])
            if in_b[b_name] != new_v:
                for pred in preds[b_name]:
                    if pred not in worklist:
                        worklist.append(pred)
                in_b[b_name] = new_v

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
                      transfer_reaching_def,
                      True)
    return in_b, out_b


def live_variables(func):

    def transfer_live_var(block, out_b):
        in_b = out_b.copy()
        # should perform operation one by one
        for instr in block[::-1]:
            if "args" in instr:
                for arg in instr["args"]:
                    in_b.add(arg)
            if "dest" in instr:
                in_b.discard(instr["dest"])
        # use_b.union(out_b - def_b)
        return in_b

    in_b, out_b = dfa(name2block,
                      set(),
                      lambda x, y: x.union(y),
                      transfer_live_var,
                      False)
    return in_b, out_b


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('-f', dest='file', default="", help='get input file')
    parser.add_argument('-reach_def', dest='reach_def', action='store_true', help='reaching definition')
    parser.add_argument('-live_var', dest='live_var', action='store_true', help='living variables')
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
    elif args.live_var:
        in_b, out_b = live_variables(func)
    else:
        raise RuntimeError("Should provide algorithm name")
    for b_name in in_b:
        print("{}:".format(b_name))
        print("  in: ", "∅" if len(in_b[b_name]) == 0 else ", ".join(in_b[b_name]))
        print("  out:", "∅" if len(out_b[b_name]) == 0 else ", ".join(out_b[b_name]))