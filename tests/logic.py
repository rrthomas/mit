# Test the logic instructions. We only test the stack handling and basic
# correctness of the instructions here, assuming that if the logic works in
# one case, it will work in all (if the C compiler doesn't implement it
# correctly, we're in trouble anyway!).
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *
from mit_test import *


# Extra constants
byte_bit = 8
bottom_byte_set = 0xff
second_byte_set = 0xff << byte_bit
penultimate_byte_set = 0xff << (word_bit - 2 * byte_bit)
top_byte_set = -1 << (word_bit - byte_bit)

# Test results
correct = []

# Code
correct.append([])
push(byte_bit)
correct.append([byte_bit])
push(top_byte_set)
correct.append([byte_bit, top_byte_set])
push(bottom_byte_set)
correct.append([byte_bit, top_byte_set, bottom_byte_set])
push(byte_bit)
correct.append([byte_bit, top_byte_set, bottom_byte_set, byte_bit])
ass(LSHIFT)
correct.append([byte_bit, top_byte_set, second_byte_set])
push(1)
correct.append([byte_bit, top_byte_set, second_byte_set, 1])
ass(SWAP)
correct.append([second_byte_set, top_byte_set, byte_bit])
ass(RSHIFT)
correct.append([second_byte_set, penultimate_byte_set])
ass(OR)
correct.append([second_byte_set | penultimate_byte_set])
ass(NOT)
correct.append([~(second_byte_set | penultimate_byte_set)])
push(1024)
correct.append([~(second_byte_set | penultimate_byte_set), 1024])
push(-1)
correct.append([~(second_byte_set | penultimate_byte_set), 1024, -1])
ass(XOR)
correct.append([~(second_byte_set | penultimate_byte_set), -1025])
ass(AND)
correct.append([~(second_byte_set | penultimate_byte_set) & -1025])
ass(NEXT)

# Test
run_test("logic", VM, correct)
