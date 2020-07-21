# Test assembly of NEXT and NEXTFF.
#
# (c) Mit authors 2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.globals import *


iterations = word_bytes * 2

for repeats in range(iterations):
    for opcode in [NEXT, NEXTFF]:
        goto(M.start)
        for _ in range(repeats):
            ass(opcode)
        pc = label()
        assert pc == M.start + word_bytes * repeats, pc - M.start

goto(M.start)
for i in range(0, iterations, 2):
    ass(NEXT)
    ass(NEXTFF)
final_pc = label()
assert final_pc == M.start + iterations * word_bytes, final_pc - M.start

print("NEXT tests ran OK")
