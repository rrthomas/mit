# Test `catch`.
#
# (c) Mit authors 2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *
from mit.enums import MitErrorCode
from mit_test import *


# Test results
correct = [
    [8],
    [8, 5],
    [8, 5, 2],
    [8, 5, 2, 2],
    [8, 5, 2, 2, M.addr + 0x200],
    [8, 5],
    [1, 3],
    [1, 3, 0],
    [1, 3, 0, 3],
    [1, 3, 0, 3, 0],
    [1, 3, 0, 3, 0, 2],
    [1, 3, 0, 3, 0, 2, 2],
    [1, 3, 0, 3, 0, 2, 2, M.addr + 0x400],
    [3, 0],
    [1, 3, 0, MitErrorCode.DIVISION_BY_ZERO],
    [1, 3, 0, MitErrorCode.DIVISION_BY_ZERO, 4],
    [],
    [0],
    [0, 0],
    [0, 0, M.addr + 0x600],
    [],
    [MitErrorCode.DIVISION_BY_ZERO],
    [MitErrorCode.DIVISION_BY_ZERO],
    [MitErrorCode.DIVISION_BY_ZERO, 0],
]

# Code
lit(8)
lit(5)
lit(2)
lit(2)
lit_pc_rel(M.addr + 0x200)
extra(CATCH)
ret_addr = label()
goto(M.addr + 0x200)

ass(DIVMOD)
ass(RET)
goto(ret_addr)

lit(3)
lit(0)
lit(2)
lit(2)
lit_pc_rel(M.addr + 0x400)
extra(CATCH)
ret_addr = label()
goto(M.addr + 0x400)

ass(DIVMOD)
ass(RET)
goto(ret_addr)

extra(STACK_DEPTH)
ass(POP)
lit(0)
lit(0)
lit_pc_rel(M.addr + 0x600)
extra(CATCH)
ret_addr = label()
goto(M.addr + 0x600)

lit(MitErrorCode.DIVISION_BY_ZERO)
extra(THROW)
goto(ret_addr)

lit(MitErrorCode.OK)
extra(THROW)

# Test
run_test("catch", VM, correct)
