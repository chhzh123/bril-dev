import sys
import json
import argparse

MEMORY_SIZE = 4096

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
        elif instr["op"] == "or":
            self.data[instr["dest"]] = self.data[instr["args"][0]] | self.data[instr["args"][1]]
        elif instr["op"] == "and":
            self.data[instr["dest"]] = self.data[instr["args"][0]] & self.data[instr["args"][1]]

    def eval_compare_op(self, instr) -> None:
        if instr["op"] == "lt":
            self.data[instr["dest"]] = self.data[instr["args"][0]] < self.data[instr["args"][1]]
        elif instr["op"] == "gt":
            self.data[instr["dest"]] = self.data[instr["args"][0]] > self.data[instr["args"][1]]
        elif instr["op"] == "eq":
            self.data[instr["dest"]] = self.data[instr["args"][0]] == self.data[instr["args"][1]]
        elif instr["op"] == "ne":
            self.data[instr["dest"]] = self.data[instr["args"][0]] != self.data[instr["args"][1]]
        elif instr["op"] == "le":
            self.data[instr["dest"]] = self.data[instr["args"][0]] <= self.data[instr["args"][1]]
        elif instr["op"] == "ge":
            self.data[instr["dest"]] = self.data[instr["args"][0]] >= self.data[instr["args"][1]]


class VirtualMachine(object):

    def __init__(self, program) -> None:
        self.funcs = program["functions"]
        funcs_map = {}
        for func in self.funcs:
            funcs_map[func["name"]] = func
            if func["name"] == "main":
                self.main = func
        self.funcs = funcs_map
        # memory facility
        self.memory = [0] * MEMORY_SIZE
        self.memory_usage = [False] * MEMORY_SIZE
        self.memory_ptr = 0
        self.allocated = {} # var->memory_size
        # garbage collection
        self.reference_count = {} # var->ref_count
        # speculative execution
        self.spec_data = {}
        # JIT tracing
        self.flag_trace = False
        self.trace = []
        self.call_ret = []
        self.instr_count = 0

    def eval(self):
        self.flag_trace = True # start from the front
        args = {}
        if "args" in self.main:
            for i, arg in enumerate(self.main["args"]):
                if arg["type"] in ["int", "bool"]:
                    val = int(input_args[i])
                elif arg["type"] == "float":
                    val = float(input_args[i])
                else:
                    raise RuntimeError("Not supported types")
                args[arg["name"]] = val
        self.eval_frame(Frame("main", self.funcs["main"]["instrs"], args))
        self.detect_memory_leak()
        self.print_trace()
        print("# of instructions:", self.instr_count)

    def eval_frame(self, frame) -> None:
        pc = 0
        while pc < len(frame.instrs):
            instr = frame.instrs[pc]
            self.instr_count += 1
            if self.flag_trace:
                self.add_instr_to_trace(instr, frame)
            # print(frame.data)
            # print(instr)
            pc += 1
            if "label" in instr:
                continue
            elif "op" in instr:
                if instr["op"] == "const":
                    frame.eval_const(instr)
                elif instr["op"] == "id":
                    frame.data[instr["dest"]] = frame.data[instr["args"][0]]
                    if instr["args"][0] in self.allocated:
                        self.reference_count[instr["args"][0]] += 1
                elif instr["op"] in ["add", "sub", "mul", "div", "or", "and"]:
                    frame.eval_binary_op(instr)
                elif instr["op"] in ["lt", "gt", "eq", "ne", "le", "ge"]:
                    frame.eval_compare_op(instr)
                elif instr["op"] == "jmp":
                    pc = frame.blocks[instr["labels"][0]]
                elif instr["op"] == "br":
                    if frame.data[instr["args"][0]]: # true
                        pc = frame.blocks[instr["labels"][0]]
                    else: # false
                        pc = frame.blocks[instr["labels"][1]]
                elif instr["op"] == "alloc": # return the address
                    # test if overwriting the original memory
                    if instr["dest"] in self.allocated:
                        self.decrease_reference_count(frame.data[instr["dest"]], instr["dest"])
                    frame.data[instr["dest"]] = self.memory_ptr
                    self.memory_ptr += frame.data[instr["args"][0]]
                    self.allocated[instr["dest"]] = frame.data[instr["args"][0]]
                    if self.memory_ptr > MEMORY_SIZE:
                        raise RuntimeError("Out of memory")
                    for loc in range(frame.data[instr["dest"]], self.memory_ptr):
                        self.memory_usage[loc] = True
                    self.reference_count[instr["dest"]] = 1
                elif instr["op"] == "free":
                    ptr = frame.data[instr["args"][0]]
                    size = self.allocated[instr["args"][0]]
                    self.free_memory(ptr, size)
                    self.reference_count[instr["args"][0]] = 0
                elif instr["op"] == "ptradd":
                    frame.data[instr["dest"]] = frame.data[instr["args"][0]] + frame.data[instr["args"][1]]
                elif instr["op"] == "load":
                    frame.data[instr["dest"]] = self.memory[frame.data[instr["args"][0]]]
                elif instr["op"] == "store":
                    self.memory[frame.data[instr["args"][0]]] = frame.data[instr["args"][1]]
                elif instr["op"] == "call":
                    args = {}
                    if "args" in instr:
                        for outer_arg, func_arg in zip(instr["args"], self.funcs[instr["funcs"][0]]["args"]):
                            args[func_arg["name"]] = frame.data[outer_arg]
                    res = self.eval_frame(Frame(instr["funcs"][0], self.funcs[instr["funcs"][0]]["instrs"], args))
                    if "dest" in instr:
                        frame.data[instr["dest"]] = res
                elif instr["op"] == "ret":
                    if "args" in instr:
                        for var in frame.data:
                            if var in self.allocated and var != instr["args"][0]:
                                self.decrease_reference_count(frame.data[var], var)
                        return frame.data[instr["args"][0]]
                    else:
                        for var in frame.data:
                            if var in self.allocated:
                                self.decrease_reference_count(frame.data[var], var)
                        return
                elif instr["op"] == "print":
                    print(frame.data[instr["args"][0]])
                # speculative execution
                elif instr["op"] == "speculate":
                    self.spec_data = frame.data.copy()
                elif instr["op"] == "commit":
                    self.spec_data = {} # done successfully
                elif instr["op"] == "guard":
                    if not frame.data[instr["args"][0]]: # exit from speculation
                        frame.data = self.spec_data.copy() # recover data
                        pc = frame.blocks[instr["labels"][0]]
                else:
                    raise RuntimeError("Unknown instruction: {}".format(instr["op"]))
        # implicit return
        for var in frame.data:
            if var in self.allocated:
                self.decrease_reference_count(frame.data[var], var)

    def decrease_reference_count(self, ptr, var):
        self.reference_count[var] -= 1
        if self.reference_count[var] == 0:
            self.free_memory(ptr, self.allocated[var])
            print("Free memory:", var)

    def free_memory(self, ptr, size):
        for loc in range(ptr, ptr+size):
            if not self.memory_usage[loc]:
                raise RuntimeError("Double free")
            self.memory_usage[loc] = False

    def detect_memory_leak(self):
        for loc in range(MEMORY_SIZE):
            if self.memory_usage[loc]:
                raise RuntimeError("Memory leak at loc {}".format(loc))

    def add_instr_to_trace(self, instr, frame):
        if "op" not in instr:
            pass
        elif instr["op"] == "jmp":
            pass
        elif instr["op"] == "br":
            if frame.data[instr["args"][0]]: # true
                jmp = instr["labels"][1]
            else:
                jmp = instr["labels"][0]
            new_instr = {"op": "guard", "args": instr["args"], "labels": [jmp]} # false branch
            self.trace.append(new_instr)
        elif instr["op"] == "call": # interprocedural
            func = self.funcs[instr["funcs"][0]]
            for i, arg in enumerate(instr["args"]):
                new_instr = {"op": "id", "dest": func["args"][i]["name"], "args": [arg], "type": func["args"][i]["type"]}
                self.trace.append(new_instr)
            self.call_ret.append((instr["dest"], instr["type"]))
        elif instr["op"] == "ret":
            new_instr = {"op": "id", "dest": self.call_ret[-1][0], "args": [instr["args"][0]], "type": self.call_ret[-1][1]}
            self.call_ret.pop()
            self.trace.append(new_instr)
        else:
            self.trace.append(instr)

    def print_trace(self):
        program = {}
        program["functions"] = [{"instrs": self.trace, "args": self.main["args"], "name": "main"}]
        with open("out.json", "w") as outfile:
            outfile.write(json.dumps(program, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process command line arguments')
    parser.add_argument('-f', dest='file', default="", help='get input file')
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    if args.file != "":
        with open(args.file, "r") as infile:
            program = json.load(infile)
        input_args = sys.argv[3:]
    else:
        program = json.loads(''.join(sys.stdin.readlines())) # already in json format
        input_args = sys.argv

    bvm = VirtualMachine(program)
    bvm.eval()