# Test the stack operators.
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Test results
correct = [
    [],
    [1],
    [1, 2],
    [1, 2, 3],
    [1, 2, 3, 0],
    [1, 2, 3, 3],
    [1, 2, 3],
    [1, 2, 3, 1],
    [1, 3, 2],
    [1, 3, 2, 1],
    [1, 3, 2, 3],
    [1, 3, 2, 3, 1],
    [1, 3, 3, 2],
    [1, 3, 3],
    [1, 3, 3, 0],
    [1, 3, 3, 3],
    [1, 3, 3, 3, 0],
    [],
    [2],
    [2, 1],
    [2, 1, 0],
    [2, 1, 1],
    [2, 1, 2],
    [2, 1, 2, 0],
    [2, 1, 2, 2],
    [2, 1, 2, 2, 0],
    [2, 1, 2, 2, 2],
]

# Test code
lit(1)
lit(2)
lit(3)
lit(0)
ass(DUP)
ass(POP)
lit(1)
ass(SWAP)
lit(1)
ass(DUP)
lit(1)
ass(SWAP)
ass(POP)
lit(0)
ass(DUP)
lit(0)
ass(SET_STACK_DEPTH)
lit(2)
lit(1)
lit(0)
ass(DUP)
ass(DUP)
lit(0)
ass(DUP)
lit(0)
ass(DUP)

# Test
for i in range(len(correct)):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(correct[i]) != str(S):
        print("Error in stack tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    _, inst = disassemble_instruction(PC.get())
    print("I = {}".format(inst))
    step()

print("Stack tests ran OK")
