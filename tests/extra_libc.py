# Test libc EXTRA calls.
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


# Data for ARGC/ARG_LEN/ARG_COPY tests
args = [b"foo", b"bard", b"basilisk"]
VM.register_args(*args)

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
    I = M[PC.get()]
    step()
    if I == LIB_C:
        break
argc = S.pop()
print("argc is {}, and should be {}".format(argc, len(args)))
if argc != len(args):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

# Test 2: LibcLib.ARG_LEN
while True:
    I = M[PC.get()]
    step()
    if I == LIB_C:
        break
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)
S.push(arg1len) # push length back for next test

# Tests 3 & 4: LibcLib.ARG_COPY
while True:
    I = M[PC.get()]
    step()
    if I == LIB_C:
        break
arg1len = S.pop()
print("arg 1's length is {}, and should be {}".format(arg1len, len(args[1])))
if arg1len != len(args[1]):
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)
c_str = string_at(libsmite.smite_native_address_of_range(VM.state, buffer, 0))
print("arg 1 is {}, and should be {}".format(c_str, args[1]))
if c_str != args[1]:
    print("Error in extra instructions tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("Extra instructions tests ran OK")
