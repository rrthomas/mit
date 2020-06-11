# Test the comparison instructions. We only test simple cases here, assuming
# that the C compiler's comparison routines will work for other cases.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *
from mit_test import *


# Utility function
def assemble_tests(inputs, outputs, op):
    assert(len(inputs) == len(outputs))
    # Assemble test and compile 'correct'
    for i, p in enumerate(inputs):
        push(p[0])
        push(p[1])
        ass(op)
        push(1)
        ass(POP)
        correct.extend(([p[0]], [p[0], p[1]], [outputs[i]], [outputs[i], 1], []))

less_than_pairs = [(3, 1),  (1, 3),  (2, 2),  (-4, 3)]
equality_pairs = [(237, 237),  (1, -1)]
correct = []

assemble_tests(less_than_pairs, [0, 1, 0, 1], LT)
assemble_tests(less_than_pairs, [0, 1, 0, 0], ULT)

run_test("comparison", VM, correct)
