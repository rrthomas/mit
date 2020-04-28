# Test State.load().
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


def try_load(file):
    try:
        load(file)
        ret = 0
    except VMError as e:
        ret = e.args[0]
    print(f"State.load() returns {ret}", end='')
    return ret

def word_to_bytes(w):
    l = []
    for i in range(word_bytes):
        l.append(w & byte_mask)
        w >>= byte_bit
    if sys.byteorder == 'big':
        l.reverse()
    return bytes(l)

def test_word():
    w = 0
    for i in range(word_bytes):
        w = w << byte_bit | (i + 1)
    return w

def object_file(word_bytes=word_bytes):
    '''
    Generate a dummy object file containing the single word 0102..{word_bytes}.
    '''
    return bytearray(word_to_bytes(test_word()))

test_file_name = 'test.obj'

def load_test(obj, error_code=0):
    '''
    Write the given binary data to a file, try to load it, and check that
    the error code is as given.
    '''
    with open(test_file_name, 'wb') as h: h.write(obj)
    res = try_load(test_file_name)
    print(f"; should be {error_code}")
    if res != error_code:
        print(f'Error in State.load() test "{test}"')
        sys.exit(1)
    if error_code == 0:
        print(f"Word 0 of memory is {M_word[M_word.addr]:#x}; should be {test_word():#x}")
        if M_word[M_word.addr] != test_word():
            print(f'Error in State.load() test "{test}"')
            sys.exit(1)


src_dir = os.environ['srcdir']


# Tests

# Test ability to load valid object files

test = 'Vanilla file'
load_test(object_file())

test = 'File with #! line'
load_test(obj = b'#!/usr/bin/mit\n' + object_file())


# Test ability to load & run saved file with assembler-generated contents
correct = [-128, 12345]
for n in correct:
    lit(n)
lit(MitErrorCode.OK)
ass(EXTRA, HALT)
save(test_file_name, length=label() - M.addr)
res = try_load(test_file_name)
print(f"; should be {MitErrorCode.OK}")
if res != MitErrorCode.OK:
    print(f'Error in State.load() test "{test}"')
    sys.exit(1)
try:
    run()
except VMError as e:
    print(f'Error in State.load() test "{test}"; error {e.args[0]}: {e.args[1]}')
    sys.exit(1)
print(f"Data stack: {S}")
print(f"Correct stack: {correct}")
if correct != list(S):
    print(f"Error in State.load() tests: pc = {VM.pc:#x}")
    sys.exit(1)


# Remove test file
os.remove(test_file_name)


print("State.load() tests ran OK")
