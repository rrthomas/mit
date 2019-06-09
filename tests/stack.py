# Test the stack instructions.
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


# Test results
correct = [
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
    [1, 3, 3],
    [1, 3],
    [1],
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
    [2, 1, 2, 2, 2, 5],
    [2, 1, 2, 2, 2, 5, 0],
    [],
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
ass(POP)
ass(POP)
ass(POP)
ass(POP)
lit(2)
lit(1)
lit(0)
ass(DUP)
ass(DUP)
lit(0)
ass(DUP)
lit(0)
ass(DUP)
ass_extra(GET_STACK_DEPTH)
ass(LIT_0)
ass_extra(SET_STACK_DEPTH)

# Test
run_test("stack", VM, correct)
