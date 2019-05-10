# Test EXT (libc and mit functions).
# FIXME: test file routines.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
VM = State()
VM.globalize(globals())


# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
VM.register_args(*args)

# Test code
buffer = 0x200
breaks = []

# Put address of buffer on stack for later
lit(buffer)
lit(16) # arbitary number > strlen(args[1])
lit(LIB_MIT_CURRENT_STATE)
lit(LIB_MIT)
ass(EXT)
lit(LIB_MIT_NATIVE_ADDRESS_OF_RANGE)
lit(LIB_MIT)
ass(EXT)

# Test LIB_C_ARGC
lit(LIB_C_ARGC)
lit(LIB_C)
ass(EXT)
breaks.append(label() + word_bytes)

# Test LIB_C_ARG
lit(1)
lit(LIB_C_ARG)
lit(LIB_C)
ass(EXT)
for i in range(align(sizeof(c_char_p)) // word_bytes):
    lit(align(sizeof(c_char_p)) // word_bytes - 1)
    ass(DUP)
lit(LIB_C_STRLEN)
lit(LIB_C)
ass(EXT)
breaks.append(label() + word_bytes)

# Test LIB_C_STRNCPY
lit(LIB_C_STRNCPY)
lit(LIB_C)
ass(EXT)
breaks.append(label() + word_bytes)

# Run LIB_C_ARGC test
step(addr=breaks[0], trace=True)
argc = S.pop()
print("argc is {}, and should be {}".format(argc, len(args)))
if argc != len(args):
    print("Error in EXT tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

# Run LIB_C_ARG test
step(addr=breaks[1], trace=True)
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in EXT tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Run LIB_C_STRNCPY test
step(addr=breaks[2], trace=True)
print("addr: {}".format(libmit.mit_native_address_of_range(VM.state, buffer, 0)))
c_str = string_at(libmit.mit_native_address_of_range(VM.state, buffer, 0))
print("arg 1 is {}, and should be {}".format(c_str, args[1]))
if c_str != args[1]:
    print("Error in EXT tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("EXT tests ran OK")
