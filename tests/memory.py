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
magic_number = 0xf201
correct = [
    [],
    [size * word_size],
    [size * word_size, word_size],
    [size * word_size, -word_size],
    [size * word_size - word_size],
    [size * word_size - word_size, magic_number],
    [size * word_size - word_size, magic_number, 1],
    [size * word_size - word_size, magic_number, size * word_size - word_size],
    [size * word_size - word_size, magic_number, size * word_size - word_size, size_word],
    [size * word_size - word_size],
    [size * word_size - word_size, 0],
    [size * word_size - word_size, size * word_size - word_size],
    [size * word_size - word_size, size * word_size - word_size, size_word],
    [size * word_size - word_size, magic_number],
    [size * word_size - word_size, magic_number, 1],
    [size * word_size - word_size],
    [size * word_size - word_size, 0],
    [size * word_size - word_size, size * word_size - word_size],
    [size * word_size - word_size, size * word_size - word_size, 1],
    [size * word_size - word_size, magic_number & 0xffff],
    [size * word_size - word_size, magic_number, 1],
    [size * word_size - word_size],
    [size * word_size - word_size, 0],
    [size * word_size - word_size, size * word_size - word_size],
    [size * word_size - word_size, size * word_size - word_size, 1],
    [size * word_size - word_size, magic_number | -0x10000],
    [size * word_size - word_size, magic_number | -0x10000, 1],
    [size * word_size - word_size],
    [size * word_size - word_size, 0],
    [size * word_size - word_size, size * word_size - word_size],
    [size * word_size - word_size, size * word_size - word_size, 0],
    [size * word_size - word_size, 1],
    [size * word_size - word_size + 1],
    [size * word_size - word_size + 1, 0],
    [0xf2],
    [0xf2, size * word_size - 1],
    [0xf2, size * word_size - 1, 0],
    [],
    [size * word_size - word_size],
    [size * word_size - word_size, size_word],
    [(0xf2 << (word_bit - byte_bit)) | magic_number | -(word_mask + 1)],
    [(0xf2 << (word_bit - byte_bit)) | magic_number | -(word_mask + 1), 1],
    [],
    [0],
    [],
]

# Test code
lit(size * word_size)
lit(word_size)
ass(NEGATE)
ass(ADD)
lit(magic_number)
lit(1)
ass(DUP)
lit(size_word)
ass(STORE)
lit(0)
ass(DUP)
lit(size_word)
ass(LOAD)
lit(1)
ass(POP)
lit(0)
ass(DUP)
lit(1)
ass(LOAD)
lit(1)
ass(POP)
lit(0)
ass(DUP)
lit(1)
ass(LOAD_SIGNED)
lit(1)
ass(POP)
lit(0)
ass(DUP)
lit(0)
ass(LOAD)
ass(ADD)
lit(0)
ass(LOAD)
lit(size * word_size - 1)
lit(0)
ass(STORE)
lit(size * word_size - word_size)
lit(size_word)
ass(LOAD)
lit(1)
ass(POP)
ass(GET_STACK_DEPTH)
ass(SET_STACK_DEPTH)

# Test
run_test("memory", VM, correct)
