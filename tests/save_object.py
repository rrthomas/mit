# Test State.save().
#
# (c) Mit authors 1995-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import os
import sys

from mit import *
memory_words = 256
VM = State(memory_words)


# Test data
VM.M_word[0] = 0x01020304
VM.M_word[word_bytes] = 0x05060708

# Test results
addr = [(memory_words + 1) * word_bytes, 0, 0]
length = [2, 5000, 2]
correct = ["invalid or unaligned address", "invalid or unaligned address", None]

# Test
def try_save(file, address, length):
    try:
        VM.save(file, address, length)
        err = None
    except Error as e:
        err = e.args[0]
    print('State.save(\"{}\", {}, {}) raises error "{}"'.format(file, address, length, err), end='')
    return err

for i in range(3):
    res = try_save("saveobj", addr[i], length[i])
    print(' should be "{}"'.format(correct[i]))
    if res != correct[i]:
        print("Error in State.save() test {}".format(i + 1))
        sys.exit(1)

RANGE = 4
assert VM.load("saveobj", RANGE * word_bytes) == length[2]
os.remove("saveobj")

for i in range(RANGE):
    old = VM.M_word[i * word_bytes]
    new = VM.M_word[(i + RANGE) * word_bytes]
    print("Word {} of memory is {}; should be {}".format(i, new, old))
    if new != old:
        print("Error in State.save() tests: loaded file does not match data saved")
        sys.exit(1)

print("State.save() tests ran OK")
