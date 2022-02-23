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
    for name in dom:
        print(name, dom[name])