import sys
import json
import argparse
from bb import form_blocks
from cfg import block_map, add_terminators, get_edges
import functools

def dominance(func):
    # find entry block
    for name in cfg:
        if len(preds[name]) == 0:
            entry = name
            break
    dom = {} # map from vertices to sets of vertices
    for name in cfg:
        dom[name] = set([name, entry])
    while True:
        old_dom = dom.copy()
        # if traverse in reverse post-order, it converges faster
        for name in cfg:
            pred_doms = [dom[pred] for pred in preds[name]]
            if len(pred_doms) != 0:
                intersection = functools.reduce(lambda x, y: x.intersection(y), pred_doms)
            else:
                intersection = set()
            dom[name] = set([name]).union(intersection)
        if old_dom == dom:
            break
    return dom

def strict_dominance(dom):
    res = dom.copy()
    for name in dom:
        res[name] = dom[name]-set([name])
    return res

def imm_dominance(sdom):
    # A immediately dominates B iff: A strictly dominates B, and A does not strictly dominates any other node that strictly dominates B (A is B’s direct parent in the dominator tree)
    idom = {}
    for node_b in sdom:
        idom[node_b] = set()
        for node_a in sdom[node_b]:
            flag = [(node_a not in sdom[other]) for other in (sdom[node_b]-set([node_a]))]
            if sum(flag) == len(sdom[node_b]) - 1:
                idom[node_b].add(node_a)
    return idom

class Node():
    def __init__(self, name):
        self.name = name
        self.children = []

    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

def dominator_tree(dom):
    name2node = {}
    root = None
    for name in dom:
        name2node[name] = Node(name)
        if len(preds[name]):
            root = name
    # get strict dominators
    sdom = strict_dominance(dom)
    # find immediate dominator
    idom = imm_dominance(sdom)
    for name in idom:
        for parent in idom[name]:
            if parent != name:
                name2node[parent].add_child(name2node[name])
    return name2node

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

    # construct cfg: name -> block
    cfg = block_map(form_blocks(func['instrs']))
    # Insert terminators into blocks that don't have them
    add_terminators(cfg)

    preds, succs = get_edges(cfg)

    dom = dominance(func)
    print("Dominators")
    for name in dom:
        print(" ", name, dom[name])
    print()

    name2node = dominator_tree(dom)
    print("Dominator tree")
    for name in name2node:
        print(" ", name, name2node[name].children)
