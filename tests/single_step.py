# Test single_step() and `next`.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.globals import *


iterations = 10
for i in range(iterations):
    print("pc = {:#x}".format(pc.get()))
    step(auto_NEXT=False)

final_pc = M.addr + iterations * word_bytes
print("pc should now be {}".format(final_pc))
if pc.get() != final_pc:
    print("Error in single_step() tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

print("single_step() tests ran OK")
