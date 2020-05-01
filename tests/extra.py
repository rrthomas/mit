# Test extra instructions and libc and libmit traps.
# TODO: test file routines.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys
from ctypes import cast, c_char_p, string_at

from mit.globals import *
from mit.binding import register_args


# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
register_args(*args)

# Test code
buffer = M.addr + 0x200
breaks = []

# Put address of buffer on stack for later
lit(buffer)

# Test ARGC
ass(NEXT, ARGC)
breaks.append(label() + word_bytes)

# Test ARGV
ass(NEXT, ARGV)
lit(word_bytes)
ass(ADD)
ass(LOAD)
lit(0)
ass(DUP)
lit(LibC.STRLEN)
lit(LIBC)
ass(TRAP)
breaks.append(label() + word_bytes)

# Test LibC.STRNCPY
lit(LibC.STRNCPY)
lit(LIBC)
ass(TRAP)
breaks.append(label() + word_bytes)


# Run ARGC test
trace(addr=breaks.pop(0))
argc = S.pop()
print(f"argc is {argc}, and should be {len(args)}")
if argc != len(args):
    print(f"Error in extra instruction and trap tests: pc = {VM.pc:#x}")
    sys.exit(1)

# Run ARGV test
trace(addr=breaks.pop(0))
arg1len = S.pop()
print(f"arg 1's length is {arg1len}, and should be {len(args[1])}")
if arg1len != len(args[1]):
    print(f"Error in extra instruction and trap tests: pc = {VM.pc:#x}")
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Run LibC.STRNCPY test
trace(addr=breaks.pop(0))
print(f"addr: {buffer:#x}")
c_str = string_at(cast(buffer, c_char_p))
print(f"arg 1 is {c_str}, and should be {args[1]}")
if c_str != args[1]:
    print(f"Error in extra instruction tests: pc = {VM.pc:#x}")
    sys.exit(1)

print("extra instruction and trap tests ran OK")
