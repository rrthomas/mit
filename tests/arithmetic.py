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

from mit.globals import *
from mit_test import *


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
    [-8],
    [-8, 7],
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
push(0)
push(1)
push(word_bytes)
push(-word_bytes)
push(-1)
ass(ADD)
ass(ADD)
ass(NEGATE)
ass(ADD)
push(0)
ass(SWAP)
push(-1)
push(word_bytes)
ass(MUL)
push(0)
ass(SWAP)
push(2)
ass(POP)
ass(NEGATE)
push(-1)
extra(DIVMOD)
push(0)
ass(SWAP)
push(2)
ass(POP)
push(word_bytes)
ass(NEGATE)
push(1)
ass(POP)
push(-8)
push(7)
extra(DIVMOD)
push(1)
ass(POP)
push(-2)
extra(UDIVMOD)
push(2)
ass(POP)
push(4)
push(2)
extra(UDIVMOD)

# Test
run_test("arithmetic", VM, correct)
