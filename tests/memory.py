# Test the memory operators. Also uses previously tested instructions.
# See errors.py for address error handling tests.
#
# (c) SMite authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
from smite_test import *
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
    [],
    [0],
    [],
    [word_size],
]

# Test code
lit(size * word_size)
lit(word_size)
ass(NEGATE)
ass(ADD)
lit(513)
lit(1)
ass(DUP)
ass(STORE)
lit(0)
ass(DUP)
ass(LOAD)
ass(POP)
lit(0)
ass(DUP)
ass(LOADB)
ass(ADD)
ass(LOADB)
lit(size * word_size - 1)
ass(STOREB)
lit(size * word_size - word_size)
ass(LOAD)
ass(POP)
ass(GET_STACK_DEPTH)
ass(SET_STACK_DEPTH)
ass(GET_WORD_SIZE)

# Test
run_test("memory", VM, correct)
