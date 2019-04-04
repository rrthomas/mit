# Test the stack operators.
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
correct = [
    [],
    [1],
    [1, 2],
    [1, 2, 3],
    [1, 2, 3, 0],
    [1, 2, 3, 3],
    [1, 2, 3],
    [1, 2, 3, 0],
    [1, 3, 2],
    [1, 3, 2, 1],
    [1, 3, 2, 3],
    [1, 3, 2, 3, 0],
    [1, 3, 3, 2],
    [1, 3, 3],
    [1, 3, 3, 0],
    [1, 3, 3, 3],
    [1, 3, 3, 3, 0],
    [],
    [2],
    [2, 1],
    [2, 1, 0],
    [2, 1, 1],
    [2, 1, 2],
    [2, 1, 2, 0],
    [2, 1, 2, 2],
    [2, 1, 2, 2, 0],
    [2, 1, 2, 2, 2],
]

# Test code
lit(1)
lit(2)
lit(3)
lit(0)
ass(DUP)
ass(POP)
lit(0)
ass(SWAP)
lit(1)
ass(DUP)
lit(0)
ass(SWAP)
ass(POP)
lit(0)
ass(DUP)
lit(0)
ass(SET_STACK_DEPTH)
lit(2)
lit(1)
lit(0)
ass(DUP)
ass(DUP)
lit(0)
ass(DUP)
lit(0)
ass(DUP)

# Test
run_test("stack", VM, correct)
