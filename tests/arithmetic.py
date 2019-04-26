# Test the arithmetic operators. Also uses the SWAP and POP instructions,
# and numbers. Since unsigned arithmetic overflow behaviour is guaranteed
# by the ISO C standard, we only test the stack handling and basic
# correctness of the operators here, assuming that if the arithmetic works
# in one case, it will work in all.
#
# (c) SMite authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
from smite_test import *
VM = State()
VM.globalize(globals())


# Test results
correct = [
    [0],
    [0, 1],
    [0, 1, word_bytes],
    [0, 1, word_bytes, -word_bytes],
    [0, 1, word_bytes, -word_bytes, -1],
    [0, 1, word_bytes, -word_bytes - 1],
    [0, 1, -1],
    [0, 1, 1],
    [0, 2],
    [0, 2, 0],
    [2, 0],
    [2, 0, -1],
    [2, 0, -1, word_bytes],
    [2, 0, -word_bytes],
    [2, 0, -word_bytes, 0],
    [2, -word_bytes, 0],
    [2, -word_bytes, 0, 2],
    [2],
    [-2],
    [-2, -1],
    [2, 0],
    [2, 0, 0],
    [0, 2],
    [0, 2, 2],
    [],
    [word_bytes],
    [-word_bytes],
    [-word_bytes, 1],
    [],
    [-word_bytes],
    [-word_bytes, word_bytes - 1],
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
lit(0)
lit(1)
lit(word_bytes)
lit(-word_bytes)
lit(-1)
ass(ADD)
ass(ADD)
ass(NEGATE)
ass(ADD)
lit(0)
ass(SWAP)
lit(-1)
lit(word_bytes)
ass(MUL)
lit(0)
ass(SWAP)
lit(2)
ass(POP)
ass(NEGATE)
lit(-1)
ass(DIVMOD)
lit(0)
ass(SWAP)
lit(2)
ass(POP)
lit(word_bytes)
ass(NEGATE)
lit(1)
ass(POP)
lit(-word_bytes)
lit(word_bytes - 1)
ass(DIVMOD)
lit(1)
ass(POP)
lit(-2)
ass(UDIVMOD)
lit(2)
ass(POP)
lit(4)
lit(2)
ass(UDIVMOD)

# Test
run_test("arithmetic", VM, correct)
