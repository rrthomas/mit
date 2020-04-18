# Test `lit`, and `lit_0` to `lit_3`; `lit_pc_rel` is tested by `branch.py`.
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
values = [
    0, 1, 2, 3,
    -257, 12345, 4, -1 << (word_bit - 1),
    1 << (word_bit - 2), -1 << (word_bit - byte_bit)
]

# Test
correct = []
for n, v in enumerate(values):
    lit(v)
    correct.append(values[:n+1])

run_test("literals", VM, correct)
