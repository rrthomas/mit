# Test the arithmetic operators. Also uses the SWAP and POP instructions,
# and numbers. Since unsigned arithmetic overflow behaviour is guaranteed
# by the ISO C standard, we only test the stack handling and basic
# correctness of the operators here, assuming that if the arithmetic works
# in one case, it will work in all.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
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
    [2, -word_size, 0, 2],
    [2],
    [-2],
    [-2, -1],
    [2, 0],
    [2, 0, 1],
    [0, 2],
    [0, 2, 2],
    [],
    [word_size],
    [-word_size],
    [-word_size, 1],
    [],
    [-word_size],
    [-word_size, word_size - 1],
    [-1, -1],
    [-1, -1, 1],
    [-1],
    [-1, -2],
    [1, 1],
    [1, 1, 2],
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
number(2)
action(POP)
action(NEGATE)
number(-1)
action(DIVMOD)
number(1)
action(SWAP)
number(2)
action(POP)
number(word_size)
action(NEGATE)
number(1)
action(POP)
number(-word_size)
number(word_size - 1)
action(DIVMOD)
number(1)
action(POP)
number(-2)
action(UDIVMOD)
number(2)
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
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Arithmetic tests ran OK")
