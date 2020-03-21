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
    print("State.load() returns {}".format(ret), end='')
    return ret

def word_to_bytes(w):
    l = []
    for i in range(word_bytes):
        l.append(w & byte_mask)
        w >>= byte_bit
    if endism == 1:
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
    print("; should be {}".format(error_code))
    if res != error_code:
        print('Error in State.load() test "{}"'.format(test))
        sys.exit(1)
    if error_code == 0:
        print("Word 0 of memory is {:#x}; should be {:#x}".format(M_word[memory.get() + 0], test_word()))
        if M_word[memory.get() + 0] != test_word():
            print('Error in State.load() test "{}"'.format(test))
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
ass(CALL, HALT)
save(test_file_name, length=assembler.label() - memory.get())
res = try_load(test_file_name)
print("; should be {}".format(0))
if res != 0:
    print('Error in State.load() test "{}"'.format(test))
    sys.exit(1)
try:
    run()
except VMError as e:
    print('Error in State.load() test "{}"; error: {}'.format(test, e.args[1]))
    sys.exit(1)
print("Data stack: {}".format(S))
print("Correct stack: {}".format(correct))
if correct != list(S):
    print("Error in State.load() tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)


# Remove test file
os.remove(test_file_name)


print("State.load() tests ran OK")
