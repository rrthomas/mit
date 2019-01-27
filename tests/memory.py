# Test the memory operators. Also uses previously tested instructions.
# See errors.py for address error handling tests.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
size = 4096
VM = State(size)
VM.globalize(globals())


# Test results
correct = [
     [],
     [size * word_size],
     [size * word_size, word_size],
     [size * word_size, -word_size],
     [size * word_size - word_size],
     [size * word_size - word_size, 513],
     [size * word_size - word_size, 513, 1],
     [size * word_size - word_size, 513, size * word_size - word_size],
     [size * word_size - word_size],
     [size * word_size - word_size, 0],
     [size * word_size - word_size, size * word_size - word_size],
     [size * word_size - word_size, 513],
     [size * word_size - word_size, 513, 1],
     [size * word_size - word_size],
     [size * word_size - word_size, 0],
     [size * word_size - word_size, size * word_size - word_size],
     [size * word_size - word_size, 1],
     [size * word_size - word_size + 1],
     [2],
     [2, size * word_size - 1],
     [],
     [size * word_size - word_size],
     [(0x02 << (word_bit - byte_bit)) | 0x0201],
     [(0x02 << (word_bit - byte_bit)) | 0x0201, 1],
     [],
     [0],
     [],
]

# Test code
action(PUSH_MEMORY)
number(word_size)
action(NEGATE)
action(ADD)
number(513)
number(1)
action(DUP)
action(STORE)
number(0)
action(DUP)
action(LOAD)
number(1)
action(POP)
number(0)
action(DUP)
action(LOADB)
action(ADD)
action(LOADB)
number(size * word_size - 1)
action(STOREB)
number(size * word_size - word_size)
action(LOAD)
number(1)
action(POP)
action(PUSH_STACK_DEPTH)
action(STORE_STACK_DEPTH)

# Test
for i in range(len(correct)):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(correct[i]) != str(S):
        print("Error in memory tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Memory tests ran OK")
