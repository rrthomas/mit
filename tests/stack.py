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
correct = [
    [1],
    [1, 2],
    [1, 2, 3],
    [1, 2, 3, 0],
    [1, 2, 3, 3],
    [1, 2, 3, 3, 1],
    [1, 2, 3],
    [1, 2, 3, 0],
    [1, 3, 2],
    [1, 3, 2, 1],
    [1, 3, 2, 3],
    [1, 3, 2, 3, 0],
    [1, 3, 3, 2],
    [1, 3, 3, 2, 1],
    [1, 3, 3],
    [1, 3, 3, 0],
    [1, 3, 3, 3],
    [1, 3, 3, 3, 4],
    [],
    [2],
    [2, 1],
    [2, 1, 0],
    [2, 1, 1],
    [2, 1, 2],
]

# Test code
push(1)
push(2)
push(3)
push(0)
ass(DUP)
push(1)
ass(POP)
push(0)
ass(SWAP)
push(1)
ass(DUP)
push(0)
ass(SWAP)
push(1)
ass(POP)
push(0)
ass(DUP)
push(4)
ass(POP)
push(2)
push(1)
push(0)
ass(DUP)
ass(DUP)

# Test
run_test("stack", VM, correct)
