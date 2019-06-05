# Test the VM-generated error codes.
#
# (c) Mit authors 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *
size = 4096
VM = State(memory_size=size, stack_size=3)
VM.globalize(globals())


# Test results and data
result = []
invalid_address = size * word_bytes + 1000
test = []

# Try to divide by zero
test.append(label())
result.append(MitError.DIVISION_BY_ZERO)
print("Test {}: PC = {}".format(len(test), test[-1]))
lit(1)
lit(0)
ass(DIVMOD)

# Try to read from an invalid stack location
test.append(label())
result.append(MitError.INVALID_STACK_READ)
print("Test {}: PC = {}".format(len(test), test[-1]))
ass(DUP)

# Try to execute an invalid memory location
test.append(label())
result.append(MitError.INVALID_MEMORY_READ)
print("Test {}: PC = {}".format(len(test), test[-1]))
lit(VM.memory_size * word_bytes + word_bytes)
ass(BRANCH)

# Try to load from an invalid address
test.append(label())
result.append(MitError.INVALID_MEMORY_READ)
print("Test {}: PC = {}".format(len(test), test[-1]))
lit(invalid_address)
lit(size_word)
ass(LOAD)

# Try to store to an invalid address
test.append(label())
result.append(MitError.INVALID_MEMORY_WRITE)
print("Test {}: PC = {}".format(len(test), test[-1]))
lit(0)
lit(invalid_address)
lit(size_word)
ass(STORE)

# Try to load from unaligned address
test.append(label())
result.append(MitError.UNALIGNED_ADDRESS)
print("Test {}: PC = {}".format(len(test), test[-1]))
lit(1)
lit(size_word)
ass(LOAD)

# Try to load with an invalid/unsupported size
test.append(label())
result.append(MitError.BAD_SIZE)
print("Test {}: PC = {}".format(len(test), test[-1]))
lit(0)
lit(42)
ass(LOAD)

# Try to store with an invalid/unsupported size
test.append(label())
result.append(MitError.BAD_SIZE)
lit(0)
lit(0)
lit(42)
ass(STORE)

# Try to execute invalid opcode
if UNDEFINED < (1 << opcode_bit):
    test.append(label())
    result.append(MitError.INVALID_OPCODE)
    print("Test {}: PC = {}".format(len(test), test[-1]))
    ass(UNDEFINED)

# Tests
assert(len(test) == len(result))

def step_trace():
    while True:
        step(trace=True)

error = 0
def do_tests(run_fn):
    global error
    for i, pc in enumerate(test):
        STACK_DEPTH.set(0)    # reset stack pointer

        print("Test {}".format(i + 1))
        I.set(0)
        PC.set(pc)
        res = 0
        try:
            run_fn()
        except ErrorCode as e:
            res = e.args[0]

        if result[i] != res:
             print("Error in errors tests: test {} failed; PC = {}".format(i + 1, PC.get()))
             print("Error code is {}; should be {}".format(res, result[i]))
             error += 1
        print()

print("Running tests with single_step")
do_tests(step_trace)
print("Running tests with run (optimized)")
do_tests(run)

# Try to write to an invalid stack location (can't do this with virtual code)
try:
    libmit.mit_store_stack(VM.state, 4, 0)
    ret = 0
except ErrorCode as e:
    ret = e.args[0]
if ret != 4:
    print("Error in errors test: test {} failed".format(i + 1))
    error += 1

if error != 0:
    sys.exit(error)

print("Errors tests ran OK")
