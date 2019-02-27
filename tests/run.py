# Test that run works, and that the return value of the HALT instruction is
# correctly returned.
#
# (c) Reuben Thomas 1995-2018
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())

if VM == None:
    print("Error in run() tests: init with valid parameters failed")
    sys.exit(1)

# Test code
number(37)
action(HALT)
final_pc = VM.here

# Test
ret = run()

return_value = 37
print("Return value should be {} and is {}".format(return_value, ret))
if ret != return_value:
    print("Error in run() tests: incorrect return value from run")
    sys.exit(1)

print("PC should now be {}".format(final_pc))
if PC.get() != final_pc:
    print("Error in run() tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("run() tests ran OK")
