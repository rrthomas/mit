# Test the comparison operators. We only test simple cases here, assuming
# that the C compiler's comparison routines will work for other cases.
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


# Utility function
def assemble_tests(inputs, outputs, op):
    assert(len(inputs) == len(outputs))
    # Assemble test and compile 'correct'
    for i, p in enumerate(inputs):
        lit(p[0])
        lit(p[1])
        ass(op)
        ass(POP)
        correct.extend(([p[0]], [p[0], p[1]], [outputs[i]], []))

less_than_pairs = [(3, 1),  (1, 3),  (2, 2),  (-4, 3)]
equality_pairs = [(237, 237),  (1, -1)]
correct = [[]]

assemble_tests(less_than_pairs, [0, 1, 0, 1], LT)
assemble_tests(equality_pairs, [1, 0], EQ)
assemble_tests(less_than_pairs, [0, 1, 0, 0], ULT)

run_test("comparison", VM, correct)
