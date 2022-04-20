import sys
import json
import argparse

def find_main(prg):
    for func in prg["functions"]:
        if func["name"] == "main":
            return func

if __name__ == "__main__":
    with open(sys.argv[1], "r") as infile:
        original_program = json.load(infile)
    with open(sys.argv[2], "r") as infile:
        traced_program = json.load(infile)
    original_instr = find_main(original_program)["instrs"]
    traced_instr = find_main(traced_program)["instrs"]
    new_instr = [{"op": "speculate"}]
    for i, instr in enumerate(traced_instr):
        if "op" in instr and instr["op"] == "guard":
            instr["labels"] = ["trace_entry"]
    new_instr.extend(traced_instr)
    new_instr.append({"op": "commit"})
    new_instr.append({"op": "jmp", "labels": ["trace_exit"]})
    new_instr.append({"label": "trace_entry"})
    new_instr.extend(original_instr)
    new_instr.append({"label": "trace_exit"})
    for i, func in enumerate(original_program["functions"]):
        if func["name"] == "main":
            original_program["functions"][i]["instrs"] = new_instr
    with open("trans.json", "w") as outfile:
        outfile.write(json.dumps(original_program, indent=2))