# Test that run() works.
#
# (c) Reuben Thomas 1995-2019
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
final_pc = word_size
ass(HALT)

# Test
ret = run() # will raise an exception on error
print("run() returned without an exception")

print("PC should now be {}".format(final_pc))
if PC.get() != final_pc:
    print("Error in run() tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("run() tests ran OK")
