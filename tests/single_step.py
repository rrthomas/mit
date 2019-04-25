# Test single_step and NOP.
#
# (c) SMite authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


iterations = 10
for i in range(iterations):
    print("PC = {:#x}".format(PC.get()))
    step()

final_pc = iterations * word_bytes
print("PC should now be {}".format(final_pc))
if PC.get() != final_pc:
    print("Error in single_step() tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("single_step() tests ran OK")
