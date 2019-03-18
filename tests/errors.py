# Test the VM-generated error codes and HALT.
#
# (c) Reuben Thomas 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
size = 4096
VM = State(memory_size=size, stack_size=3)
VM.globalize(globals())


# Test results and data
result = []
invalid_address = size * word_size + 1000
test = []

# Try to divide by zero
test.append(VM.here)
result.append(8)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
lit(1)
lit(0)
ass(DIVMOD)

# Try to set STACK_DEPTH to an invalid stack location
test.append(VM.here)
result.append(2)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
lit(STACK_SIZE.get())
ass(SET_STACK_DEPTH)
ass(GET_STACK_DEPTH)

# Try to read from an invalid stack location
test.append(VM.here)
result.append(3)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
ass(DUP)

# Try to execute an invalid memory location
test.append(VM.here)
result.append(5)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
lit(MEMORY.get() + 1)
ass(BRANCH)

# Try to load from an invalid address
test.append(VM.here)
result.append(5)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
lit(invalid_address)
ass(LOAD)

# Try to store to an invalid address
test.append(VM.here)
result.append(6)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
lit(0)
lit(invalid_address)
ass(STORE)

# Try to load from unaligned address
test.append(VM.here)
result.append(7)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
lit(1)
ass(LOAD)

# Try to execute invalid opcode
test.append(VM.here)
result.append(1)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
ass(UNDEFINED)

# Tests
assert(len(test) == len(result))
error = 0
for i in range(len(test)):
    STACK_DEPTH.set(0)    # reset stack pointer

    print("Test {}".format(i + 1))
    PC.set(test[i])
    res = 128
    while res == 128:
        print("PC = {}".format(PC.get()))
        print("S = {}".format(S))
        _, inst = disassemble_instruction(PC.get())
        print("I = {}".format(inst))
        res = step()

    if result[i] != res:
         print("Error in errors tests: test {} failed; PC = {}".format(i + 1, PC.get()))
         print("Error code is {}; should be {}".format(res, result[i]))
         error += 1
    print()

# Try to write to an invalid stack location (can't do this with virtual code)
if libsmite.smite_store_stack(VM.state, 4, 0) != 4:
    print("Error in errors test: test {} failed".format(i + 1))
    error += 1

if error != 0:
    sys.exit(error)

print("Errors tests ran OK")
