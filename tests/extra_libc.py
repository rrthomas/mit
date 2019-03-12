# Test libc extra instructions.
# FIXME: test file routines.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
VM.register_args(*args)

# Test code
buffer = 0x100

# Put address of buffer on stack for later
number(buffer)
number(16) # arbitary number > strlen(args[1])
number(LIB_SMITE_CURRENT_STATE)
action(LIB_SMITE)
number(LIB_SMITE_NATIVE_ADDRESS_OF_RANGE)
action(LIB_SMITE)

# Test LIB_C_ARGC
number(LIB_C_ARGC)
action(LIB_C)

step(addr=VM.here + 1)
argc = S.pop()
print("argc is {}, and should be {}".format(argc, len(args)))
if argc != len(args):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

# Test LIB_C_ARG
number(1)
number(LIB_C_ARG)
action(LIB_C)
for i in range(sizeof(c_char_p) // word_size):
    number(sizeof(c_char_p) // word_size - 1)
    action(DUP)
number(LIB_C_STRLEN)
action(LIB_C)

step(addr=VM.here + 1)
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Test LIB_C_STRNCPY
number(LIB_C_STRNCPY)
action(LIB_C)

step(addr=VM.here + 1)
c_str = string_at(libsmite.smite_native_address_of_range(VM.state, buffer, 0))
print("arg 1 is {}, and should be {}".format(c_str, args[1]))
if c_str != args[1]:
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("Extra instructions tests ran OK")
