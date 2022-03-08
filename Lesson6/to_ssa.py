import sys
import json
import argparse
from utils.bb import form_blocks
from utils.cfg import block_map, add_terminators, get_edges
from utils.dom import dominance, domination_frontier

def to_ssa(cfg):
    # construct definition map: variable -> block
    def_map = {}
    for block_name in cfg:
        block = cfg[block_name]
        for instr in block:
            if "dest" in instr:
                if instr["dest"] not in def_map:
                    def_map[instr["dest"]] = [block_name]
                else:
                    def_map[instr["dest"]].append(block_name)
    # insert phi node
    for var in def_map:
        def_list = def_map[var]
        ptr = 0
        while ptr < len(def_list):
            def_block = def_list[ptr]
            for frontier_block in frontiers[def_block]:
                # Add a phi-node to block, unless we have done so already.
                block = cfg[frontier_block]
                phi_node = {}
                phi_node["op"] = "phi"
                phi_node["type"] = "int"
                phi_node["args"] = [var] * len(preds[frontier_block])
                phi_node["dest"] = var
                phi_node["labels"] = []
                for pred in preds[frontier_block]:
                    phi_node["labels"].append(pred)
                if "op" not in block[0]:
                    if "op" in block[1] and block[1]["op"] != "phi":
                        block.insert(1, phi_node)
                else:
                    if "op" in block[0] and block[0]["op"] != "phi":
                        block.insert(0, phi_node)
                # Add block to Defs[v] (because it now writes to v!), unless it's already in there.
                if frontier_block not in def_list:
                    def_list.append(frontier_block)
            ptr += 1
    # get back results
    instrs = []
    for block_name in cfg:
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
        if func["name"] == "main":
            break
    else:
        raise RuntimeError("Do not have main function")

    cfg = block_map(form_blocks(func['instrs']))
    # Insert terminators into blocks that don't have them
    add_terminators(cfg)

    preds, succs = get_edges(cfg)

    dom = dominance(cfg, func, preds)
    frontiers = domination_frontier(dom, preds)

    func["instrs"] = to_ssa(cfg)
    print(json.dumps(program, indent=2))