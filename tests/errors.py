# Test the VM-generated error codes.
#
# (c) Mit authors 1995-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys
from functools import partial

from mit.globals import *
from mit.binding import stack_words_ptr


stack_words_ptr.value = 3

# Test results and data
tests = [] # (name, label, error_code)

tests.append((
    'Try to divide by zero',
    label(),
    MitErrorCode.DIVISION_BY_ZERO,
))
push(1)
push(0)
extra(DIVMOD)

tests.append((
    'Try to read from an invalid stack location',
    label(),
    MitErrorCode.INVALID_STACK_READ,
))
ass(DUP)

tests.append((
    'Try to load from unaligned address',
    label(),
    MitErrorCode.UNALIGNED_ADDRESS,
))
push(M.start + 1)
ass(LOAD)

tests.append((
    'Try to execute invalid opcode',
    label(),
    MitErrorCode.INVALID_OPCODE,
))
UNDEFINED = 0xf7
assert UNDEFINED not in Instructions.__members__.values(), Instructions.__members__.values()
ass(UNDEFINED)

# Tests
success = 0
def do_tests(run_fn):
    global success
    for name, pc_value, expected in tests:
        print(f'Test "{name}": pc = {pc_value:#x}')
        VM.pc = pc_value
        observed = 0
        try:
            run_fn()
        except VMError as e:
            observed = e.args[0]

        if observed == expected:
            success += 1
        else:
            print(f'Error in errors tests: test "{name}" failed; pc = {VM.pc:#x}')
            print(f"Error code is {observed}; should be {expected}")
        print()

print("Running tests with State.step()")
do_tests(partial(step, trace=True, addr=0))
print("Running tests with run")
do_tests(run)

if success != 2 * len(tests):
    sys.exit(error)

print("Errors tests ran OK")
