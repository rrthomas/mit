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

from mit import *
from mit_test import *
VM = State()
VM.globalize(globals())


# Extra constants
top_byte_set = -1 << (word_bit - byte_bit)
second_byte_set = 0xff << (word_bit - 2 * byte_bit)
penultimate_byte_set = 0xff << byte_bit

# Test results
correct = [
     [byte_bit, top_byte_set, penultimate_byte_set],
     [byte_bit, top_byte_set, penultimate_byte_set, 1],
     [penultimate_byte_set, top_byte_set, byte_bit],
     [penultimate_byte_set, second_byte_set],
     [second_byte_set | penultimate_byte_set],
     [~(second_byte_set | penultimate_byte_set)],
     [~(second_byte_set | penultimate_byte_set), 1],
     [~(second_byte_set | penultimate_byte_set), 1, -1],
     [~(second_byte_set | penultimate_byte_set), -2],
     [~(second_byte_set | penultimate_byte_set) & -2],
]

# Test data
S.push(byte_bit)
S.push(top_byte_set)
S.push(0xff)
S.push(byte_bit)

# Code
ass(LSHIFT)
lit(1)
ass(SWAP)
ass(RSHIFT)
ass(OR)
ass(NOT)
lit(1)
lit(-1)
ass(XOR)
ass(AND)

# Test
run_test("logic", VM, correct)
