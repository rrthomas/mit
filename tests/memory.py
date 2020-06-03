# Test the memory instructions. Also uses previously tested instructions.
# See errors.py for address error handling tests.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from sys import byteorder

from mit.globals import *
from mit_test import *


# Test results
byte_bit = 8
last_word = M_word.addr + (len(M_word) - 1) * word_bytes
magic_number = 0xf201
endism = 0 if byteorder == 'little' else 1
correct = [
    [magic_number],
    [magic_number, last_word],
    [],
    [last_word],
    [magic_number],
    [magic_number, 1],
    [],
    [last_word + (word_bytes - 2) * endism],
    [magic_number],
    [magic_number, 1],
    [],
    [last_word + (word_bytes - 2) * endism + 1 * (1 - endism)],
    [0xf2],
    [0xf2, M.addr + len(M) - ((word_bytes - 1) * endism + 1)],
    [],
    [last_word],
    [(0xf2 << (word_bit - byte_bit)) | magic_number | -(uword_max + 1)],
]

# Test code
lit(magic_number)
lit(last_word)
ass(STORE)
lit(last_word)
ass(LOAD)
lit(1)
ass(POP)
lit(last_word + (word_bytes - 2) * endism)
ass(LOAD2)
lit(1)
ass(POP)
lit(last_word + (word_bytes - 2) * endism + 1 * (1 - endism))
ass(LOAD1)
lit(M.addr + len(M) - ((word_bytes - 1) * endism + 1))
ass(STORE1)
lit(last_word)
ass(LOAD)

# Test
run_test("memory", VM, correct)
