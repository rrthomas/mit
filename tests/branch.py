# Test the branch instructions. Also uses instructions tested by
# earlier tests.
# See errors.py for address error handling tests.
# The test program contains an infinite loop, but this is only executed
# once.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
VM = State(4096)
VM.globalize(globals())


# Test results
correct = [0, 2, 96, 97, 48, 51, 10000, 10001, 10004, 10005, 10006, 10007, 10008,
           10009, 10012, 11000, 11001, 11004, 11016
]

# Code
VM.here = 0
number(96)
action(BRANCH)

VM.here = 96
number(48)
action(BRANCH)

VM.here = 48
number(10000)
action(BRANCH)

VM.here = 10000
number(1)
number(10008)
action(BRANCHZ)
number(1)
number(0)
action(BRANCHZ)
number(0)
number(11000)
action(BRANCHZ)

VM.here = 11000
number(0)
number(11016)
action(BRANCHZ)

# Test
for i in range(len(correct)):
    print("Instruction {}: PC = {} should be {}\n".format(i, PC.get(), correct[i]))
    if correct[i] != PC.get():
        print("Error in branch tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Branch tests ran OK")
