# Test the arithmetic operators. Also uses the SWAP and POP instructions,
# and numbers. Since unsigned arithmetic overflow behaviour is guaranteed
# by the ISO C standard, we only test the stack handling and basic
# correctness of the operators here, assuming that if the arithmetic works
# in one case, it will work in all.
#
# (c) Reuben Thomas 1994-2018
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
    [0],
    [0, 1],
    [0, 1, word_size],
    [0, 1, word_size, -word_size],
    [0, 1, word_size, -word_size, -1],
    [0, 1, word_size, -word_size - 1],
    [0, 1, -1],
    [0, 1, 1],
    [0, 2],
    [0, 2, 1],
    [2, 0],
    [2, 0, -1],
    [2, 0, -1, word_size],
    [2, 0, -word_size],
    [2, 0, -word_size, 1],
    [2, -word_size, 0],
    [2, -word_size],
    [2],
    [-2],
    [-2, -1],
    [2, 0],
    [2, 0, 1],
    [0, 2],
    [0],
    [],
    [word_size],
    [-word_size],
    [],
    [-word_size],
    [-word_size, word_size - 1],
    [-1, -1],
    [-1],
    [-1, -2],
    [1, 1],
    [1],
    [],
    [4],
    [4, 2],
    [2, 0],
]

# Code
number(0)
number(1)
number(word_size)
number(-word_size)
number(-1)
action(ADD)
action(ADD)
action(NEGATE)
action(ADD)
number(1)
action(SWAP)
number(-1)
number(word_size)
action(MUL)
number(1)
action(SWAP)
action(POP)
action(POP)
action(NEGATE)
number(-1)
action(DIVMOD)
number(1)
action(SWAP)
action(POP)
action(POP)
number(word_size)
action(NEGATE)
action(POP)
number(-word_size)
number(word_size - 1)
action(DIVMOD)
action(POP)
number(-2)
action(UDIVMOD)
action(POP)
action(POP)
number(4)
number(2)
action(UDIVMOD)

# Test
for i in range(len(correct)):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(correct[i]) != str(S):
        print("Error in arithmetic tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    print("I = {}".format(disassemble_instruction(PC.get())))
    step()

print("Arithmetic tests ran OK")
