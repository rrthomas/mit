# Test extra instructions (libc and mit functions).
# TODO: test file routines.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *


# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
VM.register_args(*args)

# Test code
buffer = 0x200
breaks = []

# Put address of buffer on stack for later
lit(buffer)
lit(16) # arbitary number > strlen(args[1])
lit(LibMit.CURRENT_STATE)
ass_extra(LIBMIT, type=JUMP)
lit(LibMit.NATIVE_ADDRESS_OF_RANGE)
ass_extra(LIBMIT, type=JUMP)

# Test LibC.ARGC
lit(LibC.ARGC)
lit(LIBC)
ass_extra(LIBC, type=JUMP)
breaks.append(label() + word_bytes)

# Test LibC.ARG
lit(1)
lit(LibC.ARG)
ass_extra(LIBC, type=JUMP)
for i in range(align(sizeof(c_char_p)) // word_bytes):
    lit(align(sizeof(c_char_p)) // word_bytes - 1)
    ass(DUP)
lit(LibC.STRLEN)
ass_extra(LIBC, type=JUMP)
breaks.append(label() + word_bytes)

# Test LibC.STRNCPY
lit(LibC.STRNCPY)
ass_extra(LIBC, type=JUMP)
breaks.append(label() + word_bytes)

# Run LibC.ARGC test
trace(addr=breaks[0])
argc = S.pop()
print("argc is {}, and should be {}".format(argc, len(args)))
if argc != len(args):
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

# Run LibC.ARG test
trace(addr=breaks[1])
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Run LibC.STRNCPY test
trace(addr=breaks[2])
print("addr: {}".format(libmit.mit_native_address_of_range(VM.state, buffer, 0)))
c_str = string_at(libmit.mit_native_address_of_range(VM.state, buffer, 0))
print("arg 1 is {}, and should be {}".format(c_str, args[1]))
if c_str != args[1]:
    print("Error in extra instruction tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

print("extra instruction tests ran OK")
