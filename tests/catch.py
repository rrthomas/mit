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
correct = []

# Code
correct.append([])
push(8)
correct.append([8])
push(5)
correct.append([8, 5])
push(2)
correct.append([8, 5, 2])
push(2)
correct.append([8, 5, 2, 2])
pushrel(M.addr + 0x200)
correct.append([8, 5, 2, 2, M.addr + 0x200])
extra(CATCH)
ret_addr = label()
goto(M.addr + 0x200)

correct.append([8, 5])
extra(DIVMOD)
correct.append([1, 3])
ass(RET)
goto(ret_addr)

correct.append([1, 3, 0])
push(3)
correct.append([1, 3, 0, 3])
push(0)
correct.append([1, 3, 0, 3, 0])
push(2)
correct.append([1, 3, 0, 3, 0, 2])
push(2)
correct.append([1, 3, 0, 3, 0, 2, 2])
pushrel(M.addr + 0x400)
correct.append([1, 3, 0, 3, 0, 2, 2, M.addr + 0x400])
extra(CATCH)
ret_addr = label()
goto(M.addr + 0x400)

correct.append([3, 0])
extra(DIVMOD)
# Not reached.
ass(RET)
goto(ret_addr)

correct.append([1, 3, 0, MitErrorCode.DIVISION_BY_ZERO])
ass(POP)
correct.append([1, 3, 0])
ass(POP)
correct.append([1, 3])
ass(POP)
correct.append([1])
ass(POP)
correct.append([])
push(0)
correct.append([0])
push(0)
correct.append([0, 0])
pushrel(M.addr + 0x600)
correct.append([0, 0, M.addr + 0x600])
extra(CATCH)
ret_addr = label()
goto(M.addr + 0x600)

correct.append([])
push(MitErrorCode.DIVISION_BY_ZERO)
correct.append([MitErrorCode.DIVISION_BY_ZERO])
extra(THROW)
goto(ret_addr)

correct.append([MitErrorCode.DIVISION_BY_ZERO])
push(MitErrorCode.OK)
correct.append([MitErrorCode.DIVISION_BY_ZERO, MitErrorCode.OK])
extra(THROW)

# Test
run_test("catch", VM, correct)
