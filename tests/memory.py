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
correct = []

# Test code
correct.append([])
push(magic_number)
correct.append([magic_number])
push(last_word)
correct.append([magic_number, last_word])
ass(STORE)
correct.append([])
push(last_word)
correct.append([last_word])
ass(LOAD)
correct.append([magic_number])
ass(POP)
correct.append([])
push(last_word + (word_bytes - 2) * endism)
correct.append([last_word + (word_bytes - 2) * endism])
ass(LOAD2)
correct.append([magic_number])
ass(POP)
correct.append([])
push(last_word + (word_bytes - 2) * endism + 1 * (1 - endism))
correct.append([last_word + (word_bytes - 2) * endism + 1 * (1 - endism)])
ass(LOAD1)
correct.append([magic_number >> 8])
push(M.addr + len(M) - ((word_bytes - 1) * endism + 1))
correct.append([magic_number >> 8, last_word + (word_bytes - 1) * (1 - endism)])
ass(STORE1)
correct.append([])
push(last_word)
correct.append([last_word])
ass(LOAD)
correct.append([((magic_number >> 8) << (word_bit - byte_bit)) | magic_number])
ass(NEXT)

# Test
run_test("memory", VM, correct)
