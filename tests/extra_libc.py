# Test libc EXTRA calls.
# FIXME: test file routines.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Data for ARGC/ARG_LEN/ARG_COPY tests
argc = 3
Argc_Strings = c_char_p * argc
argv = Argc_Strings(b"foo", b"bard", b"basilisk")
assert(libsmite.smite_register_args(VM.state, argc, argv) == 0)

# Test code
buffer = 0x100
number(LibcLib.ARGC)
action(LIB_C)
number(1)
number(LibcLib.ARG_LEN)
action(LIB_C)
number(1)
number(buffer)
number(16)
number(LibcLib.ARG_COPY)
action(LIB_C)

# Test 1: LibcLib.ARGC
while True:
    step()
    if I.get() == LIB_C:
        break
argc_ = S.pop()
print("argc is {}, and should be {}".format(argc_, argc))
if argc_ != argc:
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

# Test 2: LibcLib.ARG_LEN
while True:
    step()
    if I.get() == LIB_C:
        break
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(argv[1])))
if arg1len != len(argv[1]):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Tests 3 & 4: LibcLib.ARG_COPY
while True:
    step()
    if I.get() == LIB_C:
        break
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(argv[1])))
if arg1len != len(argv[1]):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)
c_str = string_at(libsmite.smite_native_address_of_range(VM.state, buffer, 0))
print("arg 1 is {}, and should be {}".format(c_str, argv[1]))
if c_str != argv[1]:
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("Extra instructions tests ran OK")
