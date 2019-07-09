# Test load_object().
#
# (c) Mit authors 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import os

from mit import *
VM = State()
VM.globalize(globals())


def try_load(file):
    try:
        load(file)
        ret = 0
    except ErrorCode as e:
        ret = e.args[0]
    print("load_object(\"{}\", 0) returns {}".format(file, ret), end='')
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
    return bytearray(b'MIT\0\0\0' + bytes([endism]) + bytes([word_bytes]) +
                     word_to_bytes(word_bytes) + word_to_bytes(test_word()))

test_file_name = 'testobj'

def write_test_file(contents):
    with open(test_file_name, 'wb') as h: h.write(contents)

def load_test(obj, error_code=0):
    '''
    Write the given binary data to a file, try to load it, and check that
    the error code is as given.
    '''
    write_test_file(obj)
    res = try_load(test_file_name)
    print(" should be {}".format(error_code))
    if res != error_code:
        print("Error in load_object() test {}".format(test))
        sys.exit(1)
    if error_code == 0:
        print("Word 0 of memory is {:#x}; should be {:#x}".format(M_word[0], test_word()))
        if M_word[0] != test_word():
            print("Error in load_object() test {}".format(test))
            sys.exit(1)


src_dir = os.environ['srcdir']


# Tests
test = 0


# Test errors when trying to load invalid object files

# Invalid magic
test += 1
obj = object_file()
obj[5] = ord('\n')
load_test(obj, LoadErrorCode.INVALID_OBJECT_FILE)

# Invalid ENDISM
test += 1
obj = object_file()
obj[6] = 4
load_test(obj, LoadErrorCode.INVALID_OBJECT_FILE)

# Insufficient data for given length
test += 1
obj = object_file()
obj[8:8 + word_bytes] = word_to_bytes(-1)
load_test(obj, LoadErrorCode.INVALID_ADDRESS_RANGE)

# Only a few bytes of header
test += 1
load_test(object_file()[0:2], LoadErrorCode.INVALID_OBJECT_FILE)

# Incorrect WORD_BYTES
wrong_word_bytes = 8 if word_bytes == 4 else 4
load_test(object_file(wrong_word_bytes), LoadErrorCode.INCOMPATIBLE_OBJECT_FILE)


# Test ability to load valid object files

# Vanilla file
test += 1
load_test(object_file())

# File with #! line
test += 1
load_test(obj = b'#!/usr/bin/mit\n' + object_file())


# Test ability to load & run saved file with assembler-generated contents
correct = [-128, 12345]
for n in correct:
    lit(n)
ass_extra(HALT)
save(test_file_name, length=assembler.label())
res = try_load(test_file_name)
print(" should be {}".format(0))
if res != 0:
    print("Error in load_object() tests: file {}".format(test_file_name))
    sys.exit(1)
try:
    run()
except ErrorCode as e:
    print("Error in load_object() tests: file {}; error: {}".format(test_file_name, e.args[1]))
    sys.exit(1)
print("Data stack: {}".format(S))
print("Correct stack: {}".format(correct))
if str(correct) != str(S):
    print("Error in load_object() tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)


# Remove test file
os.remove(test_file_name)


print("load_object() tests ran OK")
