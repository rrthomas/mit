# Test the comparison operators. We only test simple cases here, assuming
# that the C compiler's comparison routines will work for other cases.
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
correct = [0, 1, 0, 1, 1, 0, 0, 1, 0, 0]

# Code
action(LT)
action(LT)
action(LT)
action(LT)
action(EQ)
action(EQ)
action(ULT)
action(ULT)
action(ULT)
action(ULT)

# Test
def stack1():
    FRAME_DEPTH.set(0)	# empty the stack
    S.push(-4)
    S.push(3)
    S.push(2)
    S.push(2)
    S.push(1)
    S.push(3)
    S.push(3)
    S.push(1)

def stack2():
    FRAME_DEPTH.set(0)	# empty the stack
    S.push(1)
    S.push(-1)
    S.push(237)
    S.push(237)

def step(start, end):
    if end > start:
        for i in range(start, end):
            VM.step()
            print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))
            v = S.pop()
            print("Result: {}; correct result: {}\n".format(v, correct[i]))
            if correct[i] != v:
                print("Error in comparison tests: PC = {:#x}".format(PC.get()))
                sys.exit(1)

stack1()      # set up the stack with four standard pairs to compare
step(0, 4)    # do the < tests
stack2()      # set up the stack with two standard pairs to compare
step(4, 6)    # do the = tests
stack1()      # set up the stack with four standard pairs to compare
step(6, 10)   # do the U< tests

print("Comparison tests ran OK")
