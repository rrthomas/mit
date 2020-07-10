# Test the stack instructions.
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

# Test code
correct.append([])
push(1)
correct.append([1])
push(2)
correct.append([1, 2])
push(3)
correct.append([1, 2, 3])
push(0)
correct.append([1, 2, 3, 0])
ass(DUP)
correct.append([1, 2, 3, 3])
ass(POP)
correct.append([1, 2, 3])
push(0)
correct.append([1, 2, 3, 0])
ass(SWAP)
correct.append([1, 3, 2])
push(1)
correct.append([1, 3, 2, 1])
ass(DUP)
correct.append([1, 3, 2, 3])
push(0)
correct.append([1, 3, 2, 3, 0])
ass(SWAP)
correct.append([1, 3, 3, 2])
ass(POP)
correct.append([1, 3, 3])
push(0)
correct.append([1, 3, 3, 0])
ass(DUP)
correct.append([1, 3, 3, 3])
ass(POP)
correct.append([1, 3, 3])
ass(POP)
correct.append([1, 3])
ass(POP)
correct.append([1])
ass(POP)
correct.append([])
push(2)
correct.append([2])
push(1)
correct.append([2, 1])
push(0)
correct.append([2, 1, 0])
ass(DUP)
correct.append([2, 1, 1])
ass(DUP)
correct.append([2, 1, 2])
ass(NEXT)

# Test
run_test("stack", VM, correct)
