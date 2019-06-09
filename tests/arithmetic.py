# Test the arithmetic instructions. Also uses the `swap` and `pop`
# instructions, and numbers. Since unsigned arithmetic overflow behaviour is
# guaranteed by the ISO C standard, we only test the stack handling and
# basic correctness of the instructions here, assuming that if the arithmetic
# works in one case, it will work in all.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
from mit_test import *
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
    [2, -word_bytes],
    [2],
    [-2],
    [-2, -1],
    [2, 0],
    [2, 0, 0],
    [0, 2],
    [0],
    [],
    [word_bytes],
    [-word_bytes],
    [],
    [-8],
    [-8, 7],
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
ass(POP)
ass(POP)
ass(NEGATE)
lit(-1)
ass(DIVMOD)
lit(0)
ass(SWAP)
ass(POP)
ass(POP)
lit(word_bytes)
ass(NEGATE)
ass(POP)
lit(-8)
lit(7)
ass(DIVMOD)
ass(POP)
lit(-2)
ass(UDIVMOD)
ass(POP)
ass(POP)
lit(4)
lit(2)
ass(UDIVMOD)

# Test
run_test("arithmetic", VM, correct)
