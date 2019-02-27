# Test the VM-generated error codes (HALT).
#
# (c) Reuben Thomas 1995-2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
size = 4096
VM = State(memory_size=size, stack_size=3)
VM.globalize(globals())


# Test results and data
answer = 42
result = []
invalid_address = size * word_size + 1000
test = []

# Test arbitrary halt code
test.append(VM.here)
result.append(answer)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(answer)
action(HALT)

# Try to divide by zero
test.append(VM.here)
result.append(-8)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(1)
number(0)
action(DIVMOD)

# Try to set STACK_DEPTH to an invalid stack location
test.append(VM.here)
result.append(-2)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(STACK_SIZE.get())
action(SET_STACK_DEPTH)
action(GET_STACK_DEPTH)

# Try to read from an invalid stack location
test.append(VM.here)
result.append(-3)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
action(DUP)

# Try to execute an invalid memory location
test.append(VM.here)
result.append(-5)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(MEMORY.get() + 1)
action(BRANCH)

# Try to load from an invalid address
test.append(VM.here)
result.append(-5)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(invalid_address)
action(LOAD)

# Try to store to an invalid address
test.append(VM.here)
result.append(-6)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(0)
number(invalid_address)
action(STORE)

# Try to load from unaligned address
test.append(VM.here)
result.append(-7)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
number(1)
action(LOAD)

# Try to execute invalid opcode
test.append(VM.here)
result.append(-1)
print("Test {}: PC = {}".format(len(test), test[len(test) - 1]))
action(UNDEFINED)

# Tests
assert(len(test) == len(result))
error = 0
for i in range(len(test)):
    STACK_DEPTH.set(0)    # reset stack pointer

    print("Test {}".format(i + 1))
    PC.set(test[i])
    res = -128
    while res == -128:
        print("PC = {}".format(PC.get()))
        print("S = {}".format(S))
        res = step()
        print("I = {}".format(disassemble_instruction(ITYPE.get(), I.get())))

    if result[i] != res:
         print("Error in errors tests: test {} failed; PC = {}".format(i + 1, PC.get()))
         print("HALT code is {}; should be {}".format(res, result[i]))
         error += 1
    print()

# Try to write to an invalid stack location (can't do this with virtual code)
if libsmite.smite_store_stack(VM.state, 4, 0) != -4:
    print("Error in errors test: test {} failed")
    error += 1

if error != 0:
    sys.exit(error)

print("Errors tests ran OK")
