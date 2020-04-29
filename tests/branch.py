# Test the branch instructions and `lit_pc_rel`. Also uses instructions
# tested by earlier tests. See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.globals import *


# Test results
correct = []

# Code
lit(M.addr + 96)
correct.append(assembler.pc)
ass(JUMP)
goto(M.addr + 96)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(M.addr + 48)
correct.append(assembler.pc)
ass(JUMP)
goto(M.addr + 48)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(M.addr + 10000)
correct.append(assembler.pc)
ass(JUMP)
goto(M.addr + 10000)
correct.append(assembler.pc + word_bytes)

lit(1)
correct.append(assembler.pc)
lit(M.addr + 9999)
correct.append(assembler.pc)
ass(JUMPZ)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
lit(M.addr)
correct.append(assembler.pc)
ass(JUMPZ)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit_pc_rel(M.addr + 11008)
correct.append(assembler.pc)
ass(JUMPZ)
goto(M.addr + 11008)
correct.append(assembler.pc + word_bytes)

lit(0)
correct.append(assembler.pc)
lit_pc_rel(M.addr + 11008 + word_bytes * 8)
correct.append(assembler.pc)
ass(JUMPZ)
goto(M.addr + 11008 + word_bytes * 8)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(M.addr + 608)
correct.append(assembler.pc)
ass(CALL)
goto(M.addr + 608)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(M.addr + 208)
correct.append(assembler.pc)
ass(CALL)
goto(M.addr + 208)
correct.append(assembler.pc + word_bytes)

lit(M.addr + 304)
correct.append(assembler.pc)
ass(CALL)
goto(M.addr + 304)
correct.append(assembler.pc + word_bytes)

ass(JUMP)
goto(M.addr + 208 + word_bytes * 2)
correct.append(assembler.pc + word_bytes)

ass(JUMP)
goto(M.addr + 608 + word_bytes * 2)
correct.append(assembler.pc + word_bytes)

lit(M.addr + 64)
correct.append(assembler.pc)
lit(M.addr + 32)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
ass(SWAP)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
ass(DUP)
correct.append(assembler.pc)
ass(STORE)
correct.append(assembler.pc)
ass(LOAD)
correct.append(assembler.pc)
ass(CALL)
goto(M.addr + 64)
correct.append(assembler.pc + word_bytes)

# Test
for i, correct_pc in enumerate(correct):
    trace()
    print(f"Instruction {i}: pc = {VM.pc:#x} should be {correct_pc:#x}")
    if int(VM.pc) != correct_pc:
        print(f"Error in branch tests: pc = {VM.pc:#x}")
        sys.exit(1)

print("Branch tests ran OK")
