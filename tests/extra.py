# Test internal extra instructions and libc and libmit external extra
# instructions.
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
from mit.binding import libmit, register_args
from ctypes import sizeof, c_char_p, string_at


# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
register_args(*args)

# Test code
buffer = M.addr + 0x200
breaks = []

# Put address of buffer on stack for later
lit(buffer)

# Test LibMit.ARGC
lit(LibMitfeatures.ARGC)
ass(JUMP, LIBMITFEATURES)
breaks.append(label() + word_bytes)

# Test LibMit.ARGV
lit(LibMitfeatures.ARGV)
ass(JUMP, LIBMITFEATURES)
lit(word_bytes)
ass(ADD)
ass(LOAD)
lit(0)
ass(DUP)
lit(LibC.STRLEN)
ass(JUMP, LIBC)
breaks.append(label() + word_bytes)

# Test LibC.STRNCPY
lit(LibC.STRNCPY)
ass(JUMP, LIBC)
breaks.append(label() + word_bytes)


# Run LibC.ARGC test
trace(addr=breaks.pop(0))
argc = S.pop()
print("argc is {}, and should be {}".format(argc, len(args)))
if argc != len(args):
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

# Run LibC.ARGV test
trace(addr=breaks.pop(0))
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Run LibC.STRNCPY test
trace(addr=breaks.pop(0))
print("addr: {:#x}".format(buffer))
c_str = string_at(cast(buffer, c_char_p))
print("arg 1 is {}, and should be {}".format(c_str, args[1]))
if c_str != args[1]:
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

print("extra instruction tests ran OK")
