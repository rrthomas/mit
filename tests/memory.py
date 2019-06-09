# Test the memory instructions. Also uses previously tested instructions.
# See errors.py for address error handling tests.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
from mit_test import *
size = 4096
VM = State(size)
VM.globalize(globals())


# Test results
magic_number = 0xf201
correct = [
    [magic_number],
    [magic_number, (size - 1) * word_bytes],
    [magic_number, (size - 1) * word_bytes, size_word],
    [],
    [(size - 1) * word_bytes],
    [(size - 1) * word_bytes, size_word],
    [magic_number],
    [magic_number, 1],
    [],
    [(size - 1) * word_bytes + (word_bytes - 2) * endism],
    [(size - 1) * word_bytes + (word_bytes - 2) * endism, 1],
    [magic_number],
    [magic_number, 1],
    [],
    [(size - 1) * word_bytes + (word_bytes - 2) * endism],
    [(size - 1) * word_bytes + (word_bytes - 2) * endism, 1],
    [magic_number],
    [magic_number, 1],
    [magic_number | -0x10000],
    [magic_number | -0x10000, 1],
    [],
    [(size - 1) * word_bytes + (word_bytes - 2) * endism + 1 * (1 - endism)],
    [(size - 1) * word_bytes + (word_bytes - 2) * endism + 1 * (1 - endism), 0],
    [0xf2],
    [0xf2, size * word_bytes - ((word_bytes - 1) * endism + 1)],
    [0xf2, size * word_bytes - ((word_bytes - 1) * endism + 1), 0],
    [],
    [(size - 1) * word_bytes],
    [(size - 1) * word_bytes, size_word],
    [(0xf2 << (word_bit - byte_bit)) | magic_number | -(word_mask + 1)],
]

# Test code
lit(magic_number)
lit((size - 1) * word_bytes)
lit(size_word)
ass(STORE)
lit((size - 1) * word_bytes)
lit(size_word)
ass(LOAD)
lit(1)
ass(POP)
lit((size - 1) * word_bytes + (word_bytes - 2) * endism)
lit(1)
ass(LOAD)
lit(1)
ass(POP)
lit((size - 1) * word_bytes + (word_bytes - 2) * endism)
lit(1)
ass(LOAD)
lit(1)
ass(SIGN_EXTEND)
lit(1)
ass(POP)
lit((size - 1) * word_bytes + (word_bytes - 2) * endism + 1 * (1 - endism))
lit(0)
ass(LOAD)
lit(size * word_bytes - ((word_bytes - 1) * endism + 1))
lit(0)
ass(STORE)
lit((size - 1) * word_bytes)
lit(size_word)
ass(LOAD)

# Test
run_test("memory", VM, correct)
