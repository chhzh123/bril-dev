import sys
import json
import argparse
import copy
from utils.bb import form_blocks
from utils.cfg import block_map, add_terminators, get_edges
from utils.dom import dominance, domination_frontier, imm_dominance, dominator_tree

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
                # test if phi node of var has been added
                flag = False
                for instr in block:
                    if "op" in instr and instr["op"] == "phi" and instr["dest"] == var:
                        flag = True
                        break
                if not flag:
                    block.insert(0, phi_node)
                # Add block to Defs[v] (because it now writes to v!), unless it's already in there.
                if frontier_block not in def_list:
                    def_list.append(frontier_block)
            ptr += 1

    # rename variables
    stack = {}
    counter = {} # naming counter
    for var in def_map:
        stack[var] = [] # create empty stack
        counter[var] = 0
    # add function arguments
    if "args" in func:
        for arg in func["args"]:
            name = arg["name"]
            stack[name] = [name]
    def rename(block_name, stack_, counter):
        block = cfg[block_name]
        stack = copy.deepcopy(stack_)
        for instr in block:
            # replace each argument to instr with stack[old name]
            if "op" in instr and instr["op"] != "phi" and "args" in instr:
                for idx in range(len(instr["args"])):
                    old_name = instr["args"][idx]#.split(".")[0]
                    instr["args"][idx] = stack[old_name][-1]
            # replace instr's destination with a new name
            if "dest" in instr:
                old_name = instr["dest"]
                new_name = "{}.{}".format(old_name, counter[instr["dest"]])
                counter[old_name] += 1
                instr["dest"] = new_name
                # push that new name onto stack[old name]
                stack[old_name].append(new_name)
        for succ in succs[block_name]:
            for instr in cfg[succ]:
                if "op" in instr and instr["op"] == "phi":
                    # Assuming p is for a variable v, make it read from stack[v]
                    # first find the index of block in its successor's phi node
                    # and then replace the `index`-th operand of phi by stack top
                    for idx, name in enumerate(instr["labels"]):
                        if name == block_name:
                            old_name = instr["args"][idx]#.split(".")[0]
                            if len(stack[old_name]) == 0:
                                instr["args"][idx] = "__undefined"
                            else:
                                instr["args"][idx] = stack[old_name][-1]
                            break
        for imm in idom:
            if block_name in idom[imm]:
                rename(imm, stack, counter)
        # pop all the names we just pushed onto the stacks
        # since we created new stacks in the function, this should be automatically done

    rename("myentry", stack, counter)

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

        func["instrs"] = to_ssa(cfg)

    print(json.dumps(program, indent=2))