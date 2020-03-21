# Test the branch instructions and `lit_pc_rel`. Also uses instructions
# tested by earlier tests. See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Mit authors 1994-2019
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
lit(memory.get() + 96)
correct.append(assembler.pc)
ass(JUMP)
goto(memory.get() + 96)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(memory.get() + 48)
correct.append(assembler.pc)
ass(JUMP)
goto(memory.get() + 48)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(memory.get() + 10000)
correct.append(assembler.pc)
ass(JUMP)
goto(memory.get() + 10000)
correct.append(assembler.pc + word_bytes)

lit(1)
correct.append(assembler.pc)
lit(memory.get() + 9999)
correct.append(assembler.pc)
ass(JUMPZ)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
lit(memory.get() + 0)
correct.append(assembler.pc)
ass(JUMPZ)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit_pc_rel(memory.get() + 11008)
correct.append(assembler.pc)
ass(JUMPZ)
goto(memory.get() + 11008)
correct.append(assembler.pc + word_bytes)

lit(0)
correct.append(assembler.pc)
lit_pc_rel(memory.get() + 11008 + word_bytes * 8)
correct.append(assembler.pc)
ass(JUMPZ)
goto(memory.get() + 11008 + word_bytes * 8)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(memory.get() + 608)
correct.append(assembler.pc)
ass(CALL)
goto(memory.get() + 608)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(memory.get() + 208)
correct.append(assembler.pc)
ass(CALL)
goto(memory.get() + 208)
correct.append(assembler.pc + word_bytes)

lit(memory.get() + 304)
correct.append(assembler.pc)
ass(CALL)
goto(memory.get() + 304)
correct.append(assembler.pc + word_bytes)

ass(JUMP)
goto(memory.get() + 208 + word_bytes * 2)
correct.append(assembler.pc + word_bytes)

ass(JUMP)
goto(memory.get() + 608 + word_bytes * 2)
correct.append(assembler.pc + word_bytes)

lit(memory.get() + 64)
correct.append(assembler.pc)
lit(memory.get() + 32)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
ass(SWAP)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
ass(DUP)
correct.append(assembler.pc)
lit(size_word)
correct.append(assembler.pc)
ass(STORE)
correct.append(assembler.pc)
lit(size_word)
correct.append(assembler.pc)
ass(LOAD)
correct.append(assembler.pc)
ass(CALL)
goto(memory.get() + 64)
correct.append(assembler.pc + word_bytes)

# Test
for i, correct_pc in enumerate(correct):
    print("Instruction {}: pc = {} should be {}\n".format(i, pc.get(), correct_pc))
    trace()
    if pc.get() != correct_pc:
        print("Error in branch tests: pc = {:#x}".format(pc.get()))
        sys.exit(1)

print("Branch tests ran OK")
