# Test the VM-generated error codes.
#
# (c) Mit authors 1995-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
from mit.binding import libmit, libmitfeatures


VM = State(memory_words=4096, stack_words=3)
assembler = Assembler(VM)
lit = assembler.lit
label = assembler.label
ass = assembler.instruction
vars().update(VM.registers)
vars().update(Instruction.__members__)
UNDEFINED = 1 + max(Instruction)

# Test results and data
result = []
invalid_address = VM.M.memory_words() * word_bytes + 1000
test = []

# Try to divide by zero
test.append(label())
result.append(MitErrorCode.DIVISION_BY_ZERO)
print("Test {}: pc = {}".format(len(test), test[-1]))
lit(1)
lit(0)
ass(DIVMOD)

# Try to read from an invalid stack location
test.append(label())
result.append(MitErrorCode.INVALID_STACK_READ)
print("Test {}: pc = {}".format(len(test), test[-1]))
ass(DUP)

# Try to execute an invalid memory location
test.append(label())
result.append(MitErrorCode.INVALID_MEMORY_READ)
print("Test {}: pc = {}".format(len(test), test[-1]))
lit((VM.M.memory_words() + 1) * word_bytes)
ass(JUMP)

# Try to load from an invalid address
test.append(label())
result.append(MitErrorCode.INVALID_MEMORY_READ)
print("Test {}: pc = {}".format(len(test), test[-1]))
lit(invalid_address)
lit(size_word)
ass(LOAD)

# Try to store to an invalid address
test.append(label())
result.append(MitErrorCode.INVALID_MEMORY_WRITE)
print("Test {}: pc = {}".format(len(test), test[-1]))
lit(0)
lit(invalid_address)
lit(size_word)
ass(STORE)

# Try to load from unaligned address
test.append(label())
result.append(MitErrorCode.UNALIGNED_ADDRESS)
print("Test {}: pc = {}".format(len(test), test[-1]))
lit(1)
lit(size_word)
ass(LOAD)

# Try to load with an invalid/unsupported size
test.append(label())
result.append(MitErrorCode.BAD_SIZE)
print("Test {}: pc = {}".format(len(test), test[-1]))
lit(0)
lit(42)
ass(LOAD)

# Try to store with an invalid/unsupported size
test.append(label())
result.append(MitErrorCode.BAD_SIZE)
lit(0)
lit(0)
lit(42)
ass(STORE)

# Try to execute invalid opcode
if UNDEFINED < (1 << opcode_bit):
    test.append(label())
    result.append(MitErrorCode.INVALID_OPCODE)
    print("Test {}: pc = {}".format(len(test), test[-1]))
    ass(UNDEFINED)

# Tests
assert(len(test) == len(result))

def step_trace():
    while True:
        VM.trace()

error = 0
def do_tests(run_fn):
    global error
    for i, pc_value in enumerate(test):
        stack_depth.set(0)    # reset stack pointer

        print("Test {}".format(i + 1))
        ir.set(0)
        pc.set(pc_value)
        res = 0
        try:
            run_fn()
        except VMError as e:
            res = e.args[0]

        if result[i] != res:
             print("Error in errors tests: test {} failed; pc = {}".format(i + 1, pc.get()))
             print("Error code is {}; should be {}".format(res, result[i]))
             error += 1
        print()

print("Running tests with single_step")
do_tests(step_trace)
print("Running tests with run (optimized)")
do_tests(VM.run)

# Try to write to an invalid stack location (can't do this with virtual code)
try:
    libmit.mit_store_stack(VM.state, 4, 0)
    ret = 0
except VMError as e:
    ret = e.args[0]
if ret != 4:
    print("Error in errors test: test {} failed".format(i + 1))
    error += 1

if error != 0:
    sys.exit(error)

print("Errors tests ran OK")
