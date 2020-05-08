# Test run().
#
# (c) Mit authors 1995-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.globals import *


# Test code
final_pc = M.addr + word_bytes
lit(MitErrorCode.OK)
extra(HALT)

# Test
ret = run() # will raise an exception on error
print("run() returned without an exception")

print(f"pc should now be {final_pc:#x}")
if VM.pc != final_pc:
    print(f"Error in run() tests: pc = {VM.pc:#x}")
    sys.exit(1)

print("run() tests ran OK")
