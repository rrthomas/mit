# Test State.step() and `next`.
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
    print(f"pc = {VM.pc:#x}")
    step()

# The value of final_pc is caused by `run()` skipping the `break_fn` each
# time it executes `next`, and hence advancing two words.
final_pc = M.addr + (iterations * 2) * word_bytes
print(f"pc should now be {final_pc:#x}")
if VM.pc != final_pc:
    print(f"Error in single_step() tests: pc = {VM.pc:#x}")
    sys.exit(1)

print("single_step() tests ran OK")
