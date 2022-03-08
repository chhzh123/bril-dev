import sys
import json
import argparse
from .bb import form_blocks
from .cfg import block_map, add_terminators, get_edges
import functools

def dominance(cfg, func, preds):
    # find entry block
    entry = None
    for name in cfg:
        if len(preds[name]) == 0:
            entry = name
            break
    dom = {} # map from vertices to sets of vertices
    for name in cfg:
        # dom[name] = set([name]).union(set([entry]) if entry != None else set())
        if name != entry:
            dom[name] = set(cfg.keys())
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

def test_dominance(entry, dom):
    results = []
    for name in dom:
        paths = []
        dest = name

        def DFS(node, visited, path):
            nonlocal paths
            visited.append(node)
            path.append(node)
            if node == dest:
                paths.append(path.copy())
            for succ in succs[node]:
                if succ not in visited:
                    DFS(succ, visited, path)
            path.pop()
            visited.pop()

        DFS(entry, [], [])
        results.append(True)
        for path in paths:
            for dominator in dom[name]:
                if dominator not in path:
                    results[-1] = False
                    break

    if sum(results) != len(results):
        return False
    else:
        return True

def strict_dominance(dom):
    res = dom.copy()
    for name in dom:
        res[name] = dom[name]-set([name])
    return res

def imm_dominance(dom):
    # A immediately dominates B iff: A strictly dominates B, and A does not strictly dominates any other node that strictly dominates B (A is B’s direct parent in the dominator tree)
    sdom = strict_dominance(dom)
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

def dominator_tree(dom, preds):
    name2node = {}
    root = None
    for name in dom:
        name2node[name] = Node(name)
        if len(preds[name]):
            root = name
    # find immediate dominator
    idom = imm_dominance(dom)
    for name in idom:
        for parent in idom[name]:
            if parent != name:
                name2node[parent].add_child(name2node[name])
    return name2node

def domination_frontier(dom, preds):
    # A’s dominance frontier contains B iff A does not strictly dominate B, but A does dominate some predecessor of B.
    sdom = strict_dominance(dom)
    frontier = {}
    for node_a in dom:
        frontier[node_a] = set()
        for node_b in sdom:
            if node_a not in sdom[node_b]:
                for pred in preds[node_b]:
                    if node_a in dom[pred]:
                        frontier[node_a].add(node_b)
    return frontier

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
    # entry = {"label": "myentry"}
    # func['instrs'] = [entry] + func['instrs']
    cfg = block_map(form_blocks(func['instrs']))
    # Insert terminators into blocks that don't have them
    add_terminators(cfg)

    preds, succs = get_edges(cfg)

    dom = dominance(cfg, func, preds)
    if not test_dominance("entry", dom):
        raise RuntimeError("Incorrect dominance")
    print("Dominators")
    for name in dom:
        print(" ", name, dom[name])
    print()

    name2node = dominator_tree(dom, preds)
    print("Dominator tree")
    for name in name2node:
        print(" ", name, name2node[name].children)
    print()

    print("Dominance frontier")
    frontier = domination_frontier(dom, preds)
    for name in frontier:
        print(" ", name, frontier[name])
