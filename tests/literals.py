# Test LIT.
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
values = [
    -257, 12345678, 4, -1 << (word_bit - 1),
    1 << (word_bit - 2), -1 << (word_bit - byte_bit)
]

# Test
correct = []
for n, v in enumerate(values):
    lit(v)
    correct.append([values[i] for i in range(n)])

run_test("literals", VM, correct)
