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


def do_test():
    '''
    Runs the code from `VM.pc` to `assembler.pc`.
    Reads the following globals:
     - test - str - the name of the test
     - final_callback - function - passed to `trace()`
    '''
    print(f"Test {test}", file=sys.stderr)
    end = label()
    trace(addr=end + word_bytes, final_callback=final_callback)
    VM.pc = end

# Data for ARGC/ARGV tests
args = [b"foo", b"bard", b"basilisk"]
register_args(*args)

test = "ARGC"
extra(ARGC)

def final_callback(handler, stack):
    argc = stack.pop()
    handler.log(f"argc is {argc}, and should be {len(args)}")
    if argc != len(args):
        handler.log(f"Error in extra instructions and traps test {test}: pc = {handler.state.pc:#x}")
        sys.exit(1)
do_test()

test = "ARGV and LibC.STRLEN"
extra(ARGV)
push(word_bytes)
ass(ADD)
ass(LOAD)
push(LibC.STRLEN)
trap(LIBC)

def final_callback(handler, stack):
    arg1len = stack.pop()
    handler.log(f"arg 1's length is {arg1len}, and should be {len(args[1])}")
    if arg1len != len(args[1]):
        handler.log(f"Error in extra instructions and traps test {test}: pc = {handler.state.pc:#x}")
        sys.exit(1)
do_test()

test = "LibC.STRNCPY"
buffer = M.start + 0x200
push(buffer)
extra(ARGV)
push(word_bytes)
ass(ADD)
ass(LOAD)
push(len(args[1]))
push(LibC.STRNCPY)
trap(LIBC)

def final_callback(handler, stack):
    handler.log(f"addr: {buffer:#x}")
    c_str = string_at(cast(buffer, c_char_p))
    handler.log(f"arg 1 is {c_str}, and should be {args[1]}")
    if c_str != args[1]:
        handler.log(f"Error in extra instructions and traps test {test}: pc = {handler.state.pc:#x}")
        sys.exit(1)
do_test()


print("Extra instructions and trap tests ran OK")
