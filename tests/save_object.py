# Test `State.save()`.
#
# (c) Mit authors 1995-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import os
import sys

from mit.globals import *

# Test data
for i in range(2 * word_bytes):
    M[M.start + i] = i

# Test results
tests = [
    (M_word.end + word_bytes, 2, "invalid or unaligned address"),
    (M_word.start, len(M_word) + 1, "invalid or unaligned address"),
    (M_word.start, 2, None),
]

# Test
def try_save(filename, address, length):
    try:
        save(filename, address, length)
        os.remove(filename)
        res = None
    except Error as e:
        res = e.args[0]
    print(f'State.save(\"{filename}\", {address}, {length}) raises error "{res}"', end='')
    return res

FILENAME = "saveobj"
for i, (addr, length, message) in enumerate(tests):
    res = try_save(FILENAME, addr, length)
    print(f' should be "{message}"')
    if res != message:
        print(f"Error in State.save() test {i + 1}")
        sys.exit(1)

RANGE = 4
save(FILENAME, addr, RANGE)
new_addr = M_word.start + RANGE * word_bytes
load_length = load(FILENAME, new_addr)
assert load_length == RANGE, load_length
os.remove(FILENAME)

for i in range(RANGE):
    old = M_word[M_word.start + i * word_bytes]
    new = M_word[new_addr + i * word_bytes]
    print(f"Word {i} of memory is {new}; should be {old}")
    if new != old:
        print("Error in State.save() tests: loaded file does not match data saved")
        sys.exit(1)

print("State.save() tests ran OK")
