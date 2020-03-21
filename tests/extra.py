# Test extra instructions (libc and mit functions).
# TODO: test file routines.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys
from ctypes import cast

from mit.globals import *
from mit.binding import libmit
from ctypes import sizeof, c_char_p, string_at


# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
native_pointer_words = align(sizeof(c_char_p)) // word_bytes
VM.register_args(*args)

# Test code
buffer = 0x200
breaks = []

# Put address of buffer on stack for later
lit(buffer)
lit(LibMit.CURRENT_STATE)
ass(JUMP, LIBMIT)
lit(LibMit.GET_MEMORY)
ass(JUMP, LIBMIT)
ass(ADD)

# Test LibMit.NATIVE_POINTER_WORDS
lit(LibMit.NATIVE_POINTER_WORDS)
ass(JUMP, LIBMIT)
breaks.append(label() + word_bytes)

# Test LibMit.ARGC
lit(LibMit.ARGC)
ass(JUMP, LIBMIT)
breaks.append(label() + word_bytes)

# Test LibMit.ARG
lit(1)
lit(LibMit.ARG)
ass(JUMP, LIBMIT)
for i in range(native_pointer_words):
    lit(native_pointer_words - 1)
    ass(DUP)
lit(LibC.STRLEN)
ass(JUMP, LIBC)
breaks.append(label() + word_bytes)

# Test LibC.STRNCPY
lit(LibC.STRNCPY)
ass(JUMP, LIBC)
breaks.append(label() + word_bytes)


# Run LibMit.NATIVE_POINTER_WORDS test
trace(addr=breaks.pop(0))
n = S.pop()
print("NATIVE_POINTER_WORDS is {} and should be {}".format(
    n, native_pointer_words,
))
if n != native_pointer_words:
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

# Run LibC.ARGC test
trace(addr=breaks.pop(0))
argc = S.pop()
print("argc is {}, and should be {}".format(argc, len(args)))
if argc != len(args):
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

# Run LibC.ARG test
trace(addr=breaks.pop(0))
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Run LibC.STRNCPY test
trace(addr=breaks.pop(0))
print("addr: {:#x}".format(memory.get() + buffer))
c_str = string_at(cast(memory.get() + buffer, c_char_p))
print("arg 1 is {}, and should be {}".format(c_str, args[1]))
if c_str != args[1]:
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

print("extra instruction tests ran OK")
