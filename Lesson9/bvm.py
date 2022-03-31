from mimetypes import init
import sys
import json
import argparse

class Frame(object):

    def __init__(self, name, instrs, initial_data = {}) -> None:
        """
        initial_data: maps from variable name to value
        """
        self.name = name
        self.instrs = instrs
        self.data = initial_data
        self.blocks = {}
        for idx, instr in enumerate(self.instrs):
            if "label" in instr:
                self.blocks[instr["label"]] = idx

    def eval_const(self, instr) -> None:
        self.data[instr["dest"]] = instr["value"]

    def eval_binary_op(self, instr) -> None:
        if instr["op"] == "add":
            self.data[instr["dest"]] = self.data[instr["args"][0]] + self.data[instr["args"][1]]
        elif instr["op"] == "sub":
            self.data[instr["dest"]] = self.data[instr["args"][0]] - self.data[instr["args"][1]]
        elif instr["op"] == "mul":
            self.data[instr["dest"]] = self.data[instr["args"][0]] * self.data[instr["args"][1]]
        elif instr["op"] == "div":
            self.data[instr["dest"]] = self.data[instr["args"][0]] / self.data[instr["args"][1]]

    def eval_compare_op(self, instr) -> None:
        if instr["op"] == "lt":
            self.data[instr["dest"]] = self.data[instr["args"][0]] < self.data[instr["args"][1]]
        elif instr["op"] == "gt":
            self.data[instr["dest"]] = self.data[instr["args"][0]] > self.data[instr["args"][1]]
        elif instr["op"] == "eq":
            self.data[instr["dest"]] = self.data[instr["args"][0]] == self.data[instr["args"][1]]


class VirtualMachine(object):

    def __init__(self, program) -> None:
        self.funcs = program["functions"]
        funcs_map = {}
        for func in self.funcs:
            funcs_map[func["name"]] = func["instrs"]
        self.funcs = funcs_map

    def eval(self):
        self.eval_frame(Frame("main", self.funcs["main"], {}))

    def eval_frame(self, frame) -> None:
        pc = 0
        while pc < len(frame.instrs):
            instr = frame.instrs[pc]
            # print(instr)
            pc += 1
            if "label" in instr:
                continue
            elif "op" in instr:
                if instr["op"] == "const":
                    frame.eval_const(instr)
                elif instr["op"] in ["add", "sub", "mul", "div"]:
                    frame.eval_binary_op(instr)
                elif instr["op"] in ["lt", "gt", "eq"]:
                    frame.eval_compare_op(instr)
                elif instr["op"] == "jmp":
                    pc = frame.blocks[instr["labels"][0]]
                elif instr["op"] == "br":
                    if frame.data[instr["args"][0]]: # true
                        pc = frame.blocks[instr["labels"][0]]
                    else: # false
                        pc = frame.blocks[instr["labels"][1]]
                elif instr["op"] == "call":
                    self.eval_frame(Frame(instr["funcs"][0], self.funcs[instr["funcs"][0]], {}))
                elif instr["op"] == "ret":
                    return
                elif instr["op"] == "print":
                    print(frame.data[instr["args"][0]])
                else:
                    raise RuntimeError("Unknown instruction: {}".format(instr["op"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('-f', dest='file', default="", help='get input file')
    args = parser.parse_args()
    if args.file != "":
        with open(args.file, "r") as infile:
            program = json.load(infile)
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format

    bvm = VirtualMachine(program)
    bvm.eval()