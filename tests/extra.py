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
tests = [] # list of (start, end, final_callback_fn)

# Test ARGC
start = label()
extra(ARGC)

def argc_test_callback(handler, stack):
    argc = stack.pop()
    handler.trace_print(f"argc is {argc}, and should be {len(args)}")
    if argc != len(args):
        handler.trace_print(f"Error in ARGC test: pc = {handler.state.pc:#x}")
        sys.exit(1)
tests.append((start, label(), argc_test_callback))

# Test ARGV
start = label()
lit(len(args))
extra(ARGV)
lit(word_bytes)
ass(ADD)
ass(LOAD)
lit(LibC.STRLEN)
trap(LIBC)

def argv_test_callback(handler, stack):
    arg1len = stack.pop()
    handler.trace_print(f"arg 1's length is {arg1len}, and should be {len(args[1])}")
    if arg1len != len(args[1]):
        handler.trace_print(f"Error in extra instructions and trap tests: pc = {handler.state.pc:#x}")
        sys.exit(1)
tests.append((start, label(), argv_test_callback))

# Test LibC.STRNCPY
start = label()
lit(buffer)
extra(ARGV)
lit(word_bytes)
ass(ADD)
ass(LOAD)
lit(len(args[1]))
lit(LibC.STRNCPY)
trap(LIBC)

def strncpy_test_callback(handler, stack):
    handler.trace_print(f"addr: {buffer:#x}")
    c_str = string_at(cast(buffer, c_char_p))
    handler.trace_print(f"arg 1 is {c_str}, and should be {args[1]}")
    if c_str != args[1]:
        handler.trace_print(f"Error in extra instructions and trap tests: pc = {handler.state.pc:#x}")
        sys.exit(1)
tests.append((start, label(), strncpy_test_callback))


# Run tests
for i, (start, end, final_callback) in enumerate(tests):
    print(f"Test {i + 1}", file=sys.stderr)
    VM.pc = start
    trace(addr=end + word_bytes, final_callback=final_callback)

print("Extra instructions and trap tests ran OK")
