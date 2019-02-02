# Test the VM-generated exceptions and HALT codes.
#
# (c) Reuben Thomas 1995-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
size = 4096
VM = State(size)
VM.globalize(globals())


# Test results and data
answer = 42
result = [answer, -10, -9, -9, -23, -256]
invalid_address = size * word_size + 1000
address = [0, 0, size * word_size, invalid_address, 1, 0]
test = []
badpc = []

print("Test 1: PC = {}".format(VM.here))
# Test arbitrary throw code
test.append(VM.here)
badpc.append(0)
number(answer)
action(HALT)

print("Test 2: PC = {}".format(VM.here))
test.append(VM.here)
number(1)
number(0)
badpc.append(VM.here)
action(DIVMOD)
number(1)
action(POP)

print("Test 3: PC = {}".format(VM.here))
# Allow execution to run off the end of a memory area
# (test 2 has set MEMORY - 1 to all zeroes)
test.append(VM.here)
badpc.append(size * word_size)
number(MEMORY.get() - 1)
action(BRANCH)

print("Test 4: PC = {}".format(VM.here))
# Fetch from an invalid address
test.append(VM.here)
number(invalid_address)
badpc.append(VM.here)
action(LOAD)

print("Test 5: PC = {}".format(VM.here))
test.append(VM.here)
number(1)
badpc.append(VM.here)
action(LOAD)

print("Test 6: PC = {}".format(VM.here))
# Test invalid opcode
test.append(VM.here)
badpc.append(VM.here)
action(UNDEFINED)


assert(len(test) == len(badpc) == len(result) == len(address))

# Exception handler
VM.here = 200
action(HALT)
HANDLER.set(200)


# Test
error = 0
for i in range(len(test)):
    SDEPTH.set(0)    # reset stack pointer

    print("Test {}".format(i + 1))
    PC.set(test[i])
    BADPC.set(0)
    INVALID.set(0)
    res = run()

    if result[i] != res or (result[i] != 0 and badpc[i] != BADPC.get()) or ((result[i] <= -257 or result[i] == -9 or result[i] == -23) and address[i] != INVALID.get()):
         print("Error in exceptions tests: test {} failed; PC = {}".format(i + 1, PC.get()))
         print("Return code is {}; should be {}".format(res, result[i]))
         if result[i] != 0:
             print("BADPC = {}; should be {}".format(BADPC.get(), badpc[i]))
         if result[i] <= -257 or result[i] == -9 or result[i] == -23:
             print("INVALID = {}; should be {}".format(INVALID.get(), address[i]))
         error += 1
    print()

if error != 0:
    sys.exit(error)

print("Exceptions tests ran OK")
