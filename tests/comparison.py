# Test the comparison instructions. We only test simple cases here, assuming
# that the C compiler's comparison routines will work for other cases.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *
from mit_test import *


correct = []

# Utility function
def assemble_tests(inputs, outputs, op):
    assert(len(inputs) == len(outputs))
    # Assemble test and compile 'correct'
    for (left, right), result in zip(inputs, outputs):
        correct.append([])
        push(left)
        correct.append([left])
        push(right)
        correct.append([left, right])
        ass(op)
        correct.append([result])
        ass(POP)

less_than_pairs = [(3, 1),  (1, 3),  (2, 2),  (-4, 3)]
assemble_tests(less_than_pairs, [0, 1, 0, 1], LT)
assemble_tests(less_than_pairs, [0, 1, 0, 0], ULT)

equality_pairs = [(237, 237),  (1, -1)]
assemble_tests(equality_pairs, [1, 0], EQ)

run_test("comparison", VM, correct)
