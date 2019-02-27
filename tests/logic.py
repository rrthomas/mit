# Test the logic operators. We only test the stack handling and basic
# correctness of the operators here, assuming that if the logic works in
# one case, it will work in all (if the C compiler doesn't implement it
# correctly, we're in trouble anyway!).
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Extra constants
top_byte_set = -1 << (word_bit - byte_bit)
second_byte_set = 0xff << (word_bit - 2 * byte_bit)
penultimate_byte_set = 0xff << byte_bit

# Test results
correct = [
     [byte_bit, top_byte_set, 0xff, byte_bit],
     [byte_bit, top_byte_set, penultimate_byte_set],
     [byte_bit, top_byte_set, penultimate_byte_set, 2],
     [penultimate_byte_set, top_byte_set, byte_bit],
     [penultimate_byte_set, second_byte_set],
     [second_byte_set | penultimate_byte_set],
     [~(second_byte_set | penultimate_byte_set)],
     [~(second_byte_set | penultimate_byte_set), 1],
     [~(second_byte_set | penultimate_byte_set), 1, -1],
     [~(second_byte_set | penultimate_byte_set), -2],
     [~(second_byte_set | penultimate_byte_set) & -2],
]

# Test data
S.push(byte_bit)
S.push(top_byte_set)
S.push(0xff)
S.push(byte_bit)

# Code
action(LSHIFT)
number(2)
action(SWAP)
action(RSHIFT)
action(OR)
action(NOT)
number(1)
number(-1)
action(XOR)
action(AND)

# Test
for i in range(len(correct)):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(correct[i]) != str(S):
        print("Error in logic tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Logic tests ran OK")
