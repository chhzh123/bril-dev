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

    def eval(self) -> None:
        pc = 0
        while pc < len(self.instrs):
            instr = self.instrs[pc]
            # print(instr)
            pc += 1
            if "label" in instr:
                continue
            elif "op" in instr:
                if instr["op"] == "const":
                    self.eval_const(instr)
                elif instr["op"] in ["add", "sub", "mul", "div"]:
                    self.eval_binary_op(instr)
                elif instr["op"] in ["lt", "gt", "eq"]:
                    self.eval_compare_op(instr)
                elif instr["op"] == "jmp":
                    pc = self.blocks[instr["labels"][0]]
                elif instr["op"] == "br":
                    if self.data[instr["args"][0]]: # true
                        pc = self.blocks[instr["labels"][0]]
                    else: # false
                        pc = self.blocks[instr["labels"][1]]
                elif instr["op"] == "print":
                    print(self.data[instr["args"][0]])


class VirtualMachine(object):

    def __init__(self, program) -> None:
        self.funcs = program["functions"]
        for func in self.funcs:
            if func["name"] == "main":
                self.main = func
                break
        else:
            raise RuntimeError("Please provide a main function")
        self.stack = []

    def eval(self):
        self.stack.append(Frame("main", self.main["instrs"]))
        while len(self.stack) > 0:
            self.stack[-1].eval()
            self.stack.pop()


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