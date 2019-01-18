# Test the stack operators.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Test results
correct = [
    [1, 2, 3],
    [1, 2, 3, 0],
    [1, 2, 3, 3],
    [1, 2, 3, 3, 1],
    [1, 2, 3],
    [1, 2, 3, 1],
    [1, 3, 2],
    [1, 3, 2, 1],
    [1, 3, 2, 3],
    [1, 3, 2, 3, 1],
    [1, 3, 3, 2],
    [1, 3, 3, 2, 1],
    [1, 3, 3],
    [1, 3, 3, 0],
    [1, 3, 3, 3],
    [2, 1, 1],
    [2, 1, 2],
    [2, 1, 2, 0],
    [2, 1, 2, 2],
    [2, 1, 2, 2, 0],
    [2, 1, 2, 2, 2],
    [2, 1, 2, 2],
    [2, 1, 2, 2, 0],
    [2, 1, 2, 2, 2],
    [2, 1, 2, 2, 2, 2],
]


# Test data
S.push(1)
S.push(2)
S.push(3)

# Test code: first part
number(0)
action(PUSH)
number(1)
action(POP)
number(1)
action(SWAP)
number(1)
action(PUSH)
number(1)
action(SWAP)
number(1)
action(POP)
number(0)
action(PUSH)

# Test code: second part
action(PUSH)
action(PUSH)
number(0)
action(PUSH)
number(0)
action(PUSH)
action(POP2R)
number(0)
action(RPUSH)
action(RPOP)

# Test: first part
first_len = 14
for i in range(first_len):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(correct[i]) != str(S):
        print("Error in stack tests: PC = {}".format(PC))
        sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

SDEPTH.set(0)	# reset stack
S.push(2)
S.push(1)
S.push(0)		# initialise the stack

# Test: second part
for i in range(first_len, len(correct)):
    if i != first_len:
        print("Data stack: {}".format(S))
        print("Correct stack: {}\n".format(correct[i]))
        if str(correct[i]) != str(S):
            print("Error in stack tests: PC = {}".format(PC))
            sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Stack tests ran OK")
