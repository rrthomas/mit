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


def word_to_bytes(w):
    l = []
    for i in range(word_bytes):
        l.append(w & 0xff)
        w >>= 8
    if sys.byteorder == 'big':
        l.reverse()
    return bytes(l)

def test_word():
    w = 0
    for i in range(word_bytes):
        w = w << 8 | (i + 1)
    return w

def object_file(word_bytes=word_bytes):
    '''
    Generate a dummy object file containing the single word 0102..{word_bytes}.
    '''
    return bytearray(word_to_bytes(test_word()))

test_file_name = 'test.obj'

def load_test(obj):
    '''
    Write the given binary data to a file, try to load it, and check that
    the error code is as given.

     - obj - bytes
    '''
    with open(test_file_name, 'wb') as h: h.write(obj)
    load(test_file_name)
    print(f"Word 0 of memory is {M_word[M_word.start]:#x}; should be {test_word():#x}")
    if M_word[M_word.start] != test_word():
        print(f'Error in State.load() test "{test}"')
        sys.exit(1)


# Tests

# Test ability to load valid object files

test = 'Vanilla file'
load_test(object_file())

test = 'File with #! line'
load_test(obj = b'#!/usr/bin/mit\n' + object_file())


# Test ability to load & run saved file with assembler-generated contents
test = 'Assemble, save, load, run'
error_code = 42
push(error_code)
extra(THROW)
save(test_file_name, length=label() - M.start)
load(test_file_name)
try:
    run()
    res = 0
    print(f'run() exited normally; should have raised an error')
except VMError as e:
    res = e.args[0]
    print(f'Error is {res}: {e.args[1]}; should be {error_code}')
if res != error_code:
    print(f'Error in State.load() test "{test}"')
    sys.exit(1)


# Remove test file
os.remove(test_file_name)


print("State.load() tests ran OK")
