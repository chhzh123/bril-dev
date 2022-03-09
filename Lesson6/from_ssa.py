import sys
import json
import argparse
from utils.bb import form_blocks
from utils.cfg import block_map, add_terminators, get_edges
from utils.dom import dominance, domination_frontier, imm_dominance, dominator_tree

def from_ssa(cfg):
    for block_name in cfg:
        block = cfg[block_name]
        new_instr = []
        for instr in block:
            if "op" in instr and instr["op"] == "phi":
                dest = instr["dest"]
                for i, label in enumerate(instr["labels"]):
                    if instr["args"][i] != "__undefined":
                        if cfg[label][-1]["op"] in ["br", "jmp"]:
                            pos = len(cfg[label]) - 1
                        else:
                            pos = len(cfg[label])
                        cfg[label].insert(pos, {"op": "id", "args": [instr["args"][i]], "dest": dest})
            else:
                new_instr.append(instr)
        cfg[block_name] = new_instr

    # get back results
    instrs = []
    used = False
    for block_name in cfg:
        for instr in cfg[block_name]:
            if ("arg" in instr and "myentry" in instr["args"]) or ("labels" in instr and "myentry" in instr["labels"]):
                used = True
    for block_name in cfg:
        if block_name == "myentry" and not used and cfg["myentry"][0]["op"] == "jmp":
            continue
        instrs.append({"label": block_name})
        instrs.extend(cfg[block_name])
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

        # name2node = dominator_tree(dom, preds)
        # print("Dominator tree")
        # for name in name2node:
        #     print(" ", name, name2node[name].children)
        # print()

        func["instrs"] = from_ssa(cfg)

    print(json.dumps(program, indent=2))