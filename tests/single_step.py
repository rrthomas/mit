# Test single_step and NOP.
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


for i in range(10):
    action(NOP)
    print("PC = {:#x}".format(PC.get()))
    step()

final_pc = 10
print("PC should now be {}".format(final_pc))
if PC.get() != final_pc:
    print("Error in single_step() tests: PC = {:#x}".format(PC.get()))
    sys.exit(1)

print("single_step() tests ran OK")
