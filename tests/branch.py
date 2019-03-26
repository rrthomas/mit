# Test the branch instructions and LIT_PC_REL. Also uses instructions tested
# by earlier tests.
# See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State(4096)
VM.globalize(globals())


# Test results
correct = []

# Code
VM.assembler.goto(0)
correct.append(VM.assembler.pc)
lit(96)
correct.append(VM.assembler.pc)
ass(BRANCH)

VM.assembler.goto(96)
correct.append(VM.assembler.pc + word_size)
lit_pc_rel(48)
correct.append(VM.assembler.pc)
ass(BRANCH)

VM.assembler.goto(48)
correct.append(VM.assembler.pc + word_size)
lit_pc_rel(10000)
correct.append(VM.assembler.pc)
ass(BRANCH)

VM.assembler.goto(10000)
correct.append(VM.assembler.pc + word_size)
lit(1)
correct.append(VM.assembler.pc)
lit(9999)
correct.append(VM.assembler.pc)
ass(BRANCHZ)
correct.append(VM.assembler.pc)
lit(1)
correct.append(VM.assembler.pc)
lit(0)
correct.append(VM.assembler.pc)
ass(BRANCHZ)
correct.append(VM.assembler.pc)
lit(0)
correct.append(VM.assembler.pc)
lit_pc_rel(11000)
correct.append(VM.assembler.pc)
ass(BRANCHZ)

VM.assembler.goto(11000)
correct.append(VM.assembler.pc + word_size)
lit(0)
correct.append(VM.assembler.pc)
lit_pc_rel(11000 + word_size * 8)
correct.append(VM.assembler.pc)
ass(BRANCHZ)

VM.assembler.goto(11000 + word_size * 8)
correct.append(VM.assembler.pc + word_size)
lit_pc_rel(600)
correct.append(VM.assembler.pc)
ass(CALL)

VM.assembler.goto(600)
correct.append(VM.assembler.pc + word_size)
lit_pc_rel(200)
correct.append(VM.assembler.pc)
ass(CALL)

VM.assembler.goto(200)
correct.append(VM.assembler.pc + word_size)
lit(304)
correct.append(VM.assembler.pc)
ass(CALL)

VM.assembler.goto(304)
correct.append(VM.assembler.pc + word_size)
ass(BRANCH)

VM.assembler.goto(200 + word_size * 2)
correct.append(VM.assembler.pc + word_size)
ass(BRANCH)

VM.assembler.goto(600 + word_size * 2)
correct.append(VM.assembler.pc + word_size)
lit(64)
correct.append(VM.assembler.pc)
lit(24)
correct.append(VM.assembler.pc)
lit(1)
correct.append(VM.assembler.pc)
ass(SWAP)
correct.append(VM.assembler.pc)
lit(1)
correct.append(VM.assembler.pc)
ass(DUP)
correct.append(VM.assembler.pc)
ass(STORE)
correct.append(VM.assembler.pc)
ass(LOAD)
correct.append(VM.assembler.pc)
ass(CALL)
correct.append(64 + word_size)

# Test
for i, pc in enumerate(correct):
    print("Instruction {}: PC = {} should be {}\n".format(i, PC.get(), pc))
    if pc != PC.get():
        print("Error in branch tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    while registers["I"].get() & INSTRUCTION_MASK == Instructions.NEXT.value.opcode:
        step(auto_NEXT=False)
    step(trace=True, auto_NEXT=False)

print("Branch tests ran OK")
