# Test the branch instructions and LIT_PC_REL. Also uses instructions tested
# by earlier tests.
# See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
VM = State(16384)
VM.globalize(globals())


# Test results
correct = []

# Code
lit(96)
correct.append(assembler.pc)
ass(BRANCH)
goto(96)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(48)
correct.append(assembler.pc)
ass(BRANCH)
goto(48)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(10000)
correct.append(assembler.pc)
ass(BRANCH)
goto(10000)
correct.append(assembler.pc + word_bytes)

lit(1)
correct.append(assembler.pc)
lit(9999)
correct.append(assembler.pc)
ass(BRANCHZ)
correct.append(assembler.pc)
lit(1)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
ass(BRANCHZ)
correct.append(assembler.pc)
lit(0)
correct.append(assembler.pc)
lit_pc_rel(11000)
correct.append(assembler.pc)
ass(BRANCHZ)
goto(11000)
correct.append(assembler.pc + word_bytes)

lit(0)
correct.append(assembler.pc)
lit_pc_rel(11000 + word_bytes * 8)
correct.append(assembler.pc)
ass(BRANCHZ)
goto(11000 + word_bytes * 8)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(600)
correct.append(assembler.pc)
ass(CALL)
goto(600)
correct.append(assembler.pc + word_bytes)

lit_pc_rel(200)
correct.append(assembler.pc)
ass(CALL)
goto(200)
correct.append(assembler.pc + word_bytes)

lit(304)
correct.append(assembler.pc)
ass(CALL)
goto(304)
correct.append(assembler.pc + word_bytes)

ass(BRANCH)
goto(200 + word_bytes * 2)
correct.append(assembler.pc + word_bytes)

ass(BRANCH)
goto(600 + word_bytes * 2)
correct.append(assembler.pc + word_bytes)

lit(64)
correct.append(assembler.pc)
lit(24)
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
goto(64)
correct.append(assembler.pc + word_bytes)

# Test
for i, pc in enumerate(correct):
    print("Instruction {}: PC = {} should be {}\n".format(i, PC.get(), pc))
    step(trace=True)
    if pc != PC.get():
        print("Error in branch tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)

print("Branch tests ran OK")
