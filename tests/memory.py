# Test the memory instructions. Also uses previously tested instructions.
# See errors.py for address error handling tests.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *
from mit_test import *


# Test results
last_word = M_word.addr + (len(M_word) - 1) * word_bytes
magic_number = 0xf201
correct = [
    [magic_number],
    [magic_number, last_word],
    [magic_number, last_word, size_word],
    [],
    [last_word],
    [last_word, size_word],
    [magic_number],
    [magic_number, 1],
    [],
    [last_word + (word_bytes - 2) * endism],
    [last_word + (word_bytes - 2) * endism, 1],
    [magic_number],
    [magic_number, 1],
    [],
    [last_word + (word_bytes - 2) * endism],
    [last_word + (word_bytes - 2) * endism, 1],
    [magic_number],
    [magic_number, 1],
    [magic_number | -0x10000],
    [magic_number | -0x10000, 1],
    [],
    [last_word + (word_bytes - 2) * endism + 1 * (1 - endism)],
    [last_word + (word_bytes - 2) * endism + 1 * (1 - endism), 0],
    [0xf2],
    [0xf2, M.addr + len(M) - ((word_bytes - 1) * endism + 1)],
    [0xf2, M.addr + len(M) - ((word_bytes - 1) * endism + 1), 0],
    [],
    [last_word],
    [last_word, size_word],
    [(0xf2 << (word_bit - byte_bit)) | magic_number | -(word_mask + 1)],
]

# Test code
lit(magic_number)
lit(last_word)
lit(size_word)
ass(STORE)
lit(last_word)
lit(size_word)
ass(LOAD)
lit(1)
ass(POP)
lit(last_word + (word_bytes - 2) * endism)
lit(1)
ass(LOAD)
lit(1)
ass(POP)
lit(last_word + (word_bytes - 2) * endism)
lit(1)
ass(LOAD)
lit(1)
ass(SIGN_EXTEND)
lit(1)
ass(POP)
lit(last_word + (word_bytes - 2) * endism + 1 * (1 - endism))
lit(0)
ass(LOAD)
lit(M.addr + len(M) - ((word_bytes - 1) * endism + 1))
lit(0)
ass(STORE)
lit(last_word)
lit(size_word)
ass(LOAD)

# Test
run_test("memory", VM, correct)
