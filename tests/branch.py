# Test the branch instructions and LIT_PC_REL. Also uses instructions tested
# by earlier tests.
# See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State(4096)
VM.globalize(globals())


# Test results
correct = [0, word_size + 1, 96, 96 + word_size + 1, 48, 48 + word_size + 1,
           10000, 10000 + word_size + 1, 10000 + word_size * 2 + 2,
           10000 + word_size * 2 + 3, 10000 + word_size * 3 + 4, 10000 + word_size * 4 + 5,
           10000 + word_size * 4 + 6, 10000 + word_size * 5 + 7, 10000 + word_size * 6 + 8,
           11000, 11000 + word_size + 1, 11000 + word_size * 2 + 2, 11000 + word_size * 8, 11000 + word_size * 9 + 1,
           600, 600 + word_size + 1,
           200, 200 + word_size + 1, 300,
           200 + word_size + 2,
           600 + word_size + 2, 600 + word_size * 2 + 3, 600 + word_size * 3 + 4, 600 + word_size * 4 + 5,
           600 + word_size * 4 + 6, 600 + word_size * 5 + 7, 600 + word_size * 5 + 8,
           600 + word_size * 5 + 9, 600 + word_size * 5 + 10, 64
]

# Code
VM.here = 0
lit(96)
ass(BRANCH)

VM.here = 96
lit_pc_rel(48)
ass(BRANCH)

VM.here = 48
lit_pc_rel(10000)
ass(BRANCH)

VM.here = 10000
lit(1)
lit(9999)
ass(BRANCHZ)
lit(1)
lit(0)
ass(BRANCHZ)
lit(0)
lit_pc_rel(11000)
ass(BRANCHZ)

VM.here = 11000
lit(0)
lit_pc_rel(11000 + word_size * 8)
ass(BRANCHZ)

VM.here = 11000 + word_size * 8
lit_pc_rel(600)
ass(CALL)

VM.here = 600
lit_pc_rel(200)
ass(CALL)
lit(64)
lit(24)
lit(1)
ass(SWAP)
lit(1)
ass(DUP)
ass(STORE)
ass(LOAD)
ass(CALL)

VM.here = 200
lit(300)
ass(CALL)
ass(BRANCH)

VM.here = 300
ass(BRANCH)

# Test
for i in range(len(correct)):
    print("Instruction {}: PC = {} should be {}\n".format(i, PC.get(), correct[i]))
    if correct[i] != PC.get():
        print("Error in branch tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    print("I = {}".format(disassemble_instruction(PC.get())))
    step()

print("Branch tests ran OK")
