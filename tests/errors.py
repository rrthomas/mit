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

from mit import *
from mit.binding import libmit, stack_words_ptr


VM = State(memory_words=4096)
stack_words_ptr.value = 3
assembler = Assembler(VM)
lit = assembler.lit
label = assembler.label
ass = assembler.instruction
vars().update(Instructions.__members__)
UNDEFINED = 0x20 << 2
assert UNDEFINED not in Instructions.__members__.values(), Instructions.__members__.values()

# Test results and data
result = []
invalid_address = VM.M.addr + len(VM.M) + 1000
test = []
test_pc = []

test.append('Try to divide by zero')
test_pc.append(label())
result.append(MitErrorCode.DIVISION_BY_ZERO)
print(f'Test "{test[-1]}": pc = {test_pc[-1]:#x}')
lit(1)
lit(0)
ass(DIVMOD)

test.append('Try to read from an invalid stack location')
test_pc.append(label())
result.append(MitErrorCode.INVALID_STACK_READ)
print(f'Test "{test[-1]}": pc = {test_pc[-1]:#x}')
ass(DUP)

test.append('Try to load from unaligned address')
test_pc.append(label())
result.append(MitErrorCode.UNALIGNED_ADDRESS)
print(f'Test "{test[-1]}": pc = {test_pc[-1]:#x}')
lit(VM.M.addr + 1)
ass(LOAD)

test.append('Try to execute invalid opcode')
test_pc.append(label())
result.append(MitErrorCode.INVALID_OPCODE)
print(f'Test "{test[-1]}": pc = {test_pc[-1]:#x}')
ass(UNDEFINED)

# Tests
assert(len(test_pc) == len(result))

error = 0
def do_tests(run_fn):
    global error
    for i, pc_value in enumerate(test_pc):
        print(f'Test "{test[i]}"')
        VM.pc = pc_value
        res = 0
        try:
            run_fn()
        except VMError as e:
            res = e.args[0]

        if result[i] != res:
             print(f'Error in errors tests: test "{test[i]}" failed; pc = {VM.pc:#x}')
             print(f"Error code is {res}; should be {result[i]}")
             error += 1
        print()

print("Running tests with State.step()")
do_tests(partial(VM.step, trace=True, addr=0))
print("Running tests with run (optimized)")
do_tests(VM.run)

if error != 0:
    sys.exit(error)

print("Errors tests ran OK")
