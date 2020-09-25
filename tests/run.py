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
final_pc = M.start + word_bytes
error_code = 42
push(error_code)
extra(THROW)

# Test
try:
    ret = run() # will raise an exception on error
    print("Error in run() tests: run() did not return an error when it should have")
    sys.exit(1)
except VMError as e:
    if e.args[0] != error_code:
        print(f"Error in run() tests: error code {e.args[0]} returned; expected {error_code}")
        sys.exit(1)

print("run() tests ran OK")
