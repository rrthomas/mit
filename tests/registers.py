# Test the register instructions, except for those operating on RDEPTH and
# SDEPTH (see memory.py).
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
size = 1024
VM = State(size)
VM.globalize(globals())


# Test results
correct = [
    [],
    [1],
    [1, 1],
    [],
    [16384],
    [16384, 1],
    [],
    [default_stack_size],
    [default_stack_size, 1],
    [],
    [size * word_size],
    [size * word_size, 1],
    [],
    [word_size],
    [word_size, native_pointer_size],
    [word_size, native_pointer_size, 2],
    [],
]

# Test code
action(PUSH_PC)
number(1)
action(POP)
action(PUSH_SSIZE)
number(1)
action(POP)
action(PUSH_RSIZE)
number(1)
action(POP)
action(PUSH_MEMORY)
number(1)
action(POP)
action(PUSH_WORD_SIZE)
action(PUSH_NATIVE_POINTER_SIZE)
number(2)
action(POP)

# Test
for i in range(len(correct)):
    print("Data stack: {}".format(S))
    print("Correct stack: {}\n".format(correct[i]))
    if str(S) != str(correct[i]):
        print("Error in registers tests: PC = {:#x}".format(PC.get()))
        sys.exit(1)
    step()
    print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

print("Registers tests ran OK")
