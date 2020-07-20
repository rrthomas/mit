# Test the arithmetic instructions. Also uses the `swap` and `pop`
# instructions, and numbers. Since unsigned arithmetic overflow behaviour is
# guaranteed by the ISO C standard, we only test the stack handling and
# basic correctness of the instructions here, assuming that if the arithmetic
# works in one case, it will work in all.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *
from mit_test import *


# Test results
correct = []

# Code
correct.append([])
push(0)
correct.append([0])
push(1)
correct.append([0, 1])
push(word_bytes)
correct.append([0, 1, word_bytes])
push(-word_bytes)
correct.append([0, 1, word_bytes, -word_bytes])
push(-1)
correct.append([0, 1, word_bytes, -word_bytes, -1])
ass(ADD)
correct.append([0, 1, word_bytes, -word_bytes - 1])
ass(ADD)
correct.append([0, 1, -1])
ass(NEG)
correct.append([0, 1, 1])
ass(ADD)
correct.append([0, 2])
push(0)
correct.append([0, 2, 0])
ass(SWAP)
correct.append([2, 0])
push(-1)
correct.append([2, 0, -1])
push(word_bytes)
correct.append([2, 0, -1, word_bytes])
ass(MUL)
correct.append([2, 0, -word_bytes])
ass(POP)
correct.append([2, 0])
ass(POP)
correct.append([2])
ass(NEG)
correct.append([-2])
push(-1)
correct.append([-2, -1])
extra(DIVMOD)
correct.append([2, 0])
ass(POP)
correct.append([2])
ass(POP)
correct.append([])
push(-8)
correct.append([-8])
push(7)
correct.append([-8, 7])
extra(DIVMOD)
correct.append([-1, -1])
ass(POP)
correct.append([-1])
push(-2)
correct.append([-1, -2])
extra(UDIVMOD)
correct.append([1, 1])
ass(POP)
correct.append([1])
ass(POP)
correct.append([])
push(4)
correct.append([4])
push(2)
correct.append([4, 2])
extra(UDIVMOD)
correct.append([2, 0])
ass(NEXT)

# Test
run_test("arithmetic", VM, correct)
