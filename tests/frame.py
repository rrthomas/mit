# Test the frame instructions.
#
# (c) Reuben Thomas 2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Test code and results
answer = 42
initial_F0 = 0
correct = [ [] ]

# Test PUSH_FRAME and POP_FRAME
correct += [
    [0],
    [0, answer],
    [answer, initial_F0],
    [answer, initial_F0, 1],
    [answer, initial_F0, 1, 2],
    [answer, initial_F0, 1, 2, 3],
    [1, 2, 3, answer],
    [1, 2, 3, answer, 4],
    [],
]
number(0)
number(answer)
action(PUSH_FRAME)
number(1)
number(2)
number(3)
action(POP_FRAME)
action(PUSH_FRAME_DEPTH)
action(POP)

# Test LOAD_OUTER_F0, LOAD_FRAME_VALUE, LOAD_OUTER_DEPTH
correct += [
    [0],
    [0, answer],
    [answer, initial_F0],
    [answer, initial_F0, initial_F0 + frame_info_words],
    [answer, initial_F0, initial_F0],
    [answer, initial_F0, initial_F0, 1],
    [answer, initial_F0],
    [answer, initial_F0, initial_F0 + frame_info_words],
    [answer, initial_F0, answer],
    [answer, initial_F0, answer, 1],
    [answer, initial_F0],
    [answer, initial_F0, 1],
    [answer, initial_F0, 1, 2],
    [answer, initial_F0, 1, 2, 3],
    [answer, initial_F0, 1, 2, 3, initial_F0 + frame_info_words],
    [answer, initial_F0, 1, 2, 3, 0],
    [1, 2, 3, 0, answer],
    [1, 2, 3, 0, answer, 5],
    [],
]
number(0)
number(answer)
action(PUSH_FRAME)
action(PUSH_F0)
action(LOAD_OUTER_F0)
number(1)
action(POP)
action(PUSH_F0)
action(LOAD_FRAME_VALUE)
number(1)
action(POP)
number(1)
number(2)
number(3)
action(PUSH_F0)
action(LOAD_OUTER_DEPTH)
action(POP_FRAME)
action(PUSH_FRAME_DEPTH)
action(POP)

# Test FRAME_DUP, FRAME_SWAP on current frame
correct += [
    [1],
    [1, 2],
    [1, 2, 3],
    [1, 2, 3, 1],
    [1, 2, 3, 1, initial_F0],
    [1, 2, 3, 2],
    [1, 2, 3, 2, 2],
    [1, 2, 3, 2, 2, initial_F0],
    [1, 2, 2, 3],
]
number(1)
number(2)
number(3)
number(1)
action(PUSH_F0)
action(FRAME_DUP)
number(2)
action(PUSH_F0)
action(FRAME_SWAP)

# Test FRAME_DUP, FRAME_SWAP on inner frame
correct += [
    [1, 2, 2, 3, 0],
    [1, 2, 2, 3, 0, 1],
    [1, 2, 2, 0, 3],
    [1, 2, 2, 3, initial_F0],
    [1, 2, 2, 3, initial_F0, initial_F0 + frame_info_words + 3],
    [1, 2, 2, 3, initial_F0, initial_F0],
    [1, 2, 2, 3, initial_F0, initial_F0, 0],
    [1, 2, 2, 3, initial_F0, 1],
    [1, 2, 2, 3, initial_F0, 1, initial_F0 + frame_info_words + 3],
    [1, 2, 2, 3, initial_F0, 1, initial_F0],
    [1, 2, 2, 3, initial_F0, 1, initial_F0, 1],
    [1, 1, 2, 3, initial_F0, 2],
    [1, 1, 2, 2, 3],
]
number(0)
number(1)
action(SWAP)
action(PUSH_FRAME)
action(PUSH_F0)
action(LOAD_OUTER_F0)
number(0)
action(FRAME_DUP)
action(PUSH_F0)
action(LOAD_OUTER_F0)
number(1)
action(FRAME_SWAP)
action(POP_FRAME)

# Test CALL
subroutine = 1000
number(subroutine)
action(CALL)
correct += [
    [1, 1, 2, 2, 3, subroutine],
    [1, VM.here, initial_F0, 1, 2, 2],
    [1, VM.here, initial_F0, 1, 2, 2, 3],
    [1, 1, 2, 2, 3, VM.here],
    [1, 1, 2, 2, 3],
    [1, 1, 2, 2, 3, answer],
    [1, 1, 2, 2, 3, answer, 6],
    [],
]
number(answer)
action(PUSH_FRAME_DEPTH)
action(POP)

# Test PUSH_F0 and STORE_F0
# (At the end so that executing STORE_FO does not mess things up!)
correct += [
    [0],
    [0, 1],
    [],
    [answer],
    [42, 1, 2, 2, 3, 42, 6, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
action(PUSH_F0)
number(1)
action(POP)
number(answer)
action(STORE_F0)
action(PUSH_F0)

VM.here = subroutine
number(3)
action(POP_FRAME)
action(BRANCH)

# Test
for i in range(len(correct)):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(S) != str(correct[i]):
        print("Error in frame tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Frame tests ran OK")
