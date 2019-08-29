# Test run().
#
# (c) Mit authors 1995-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *


# Test code
final_pc = word_bytes
ass(CALL, HALT)

# Test
ret = run() # will raise an exception on error
print("run() returned without an exception")

print("pc should now be {}".format(final_pc))
if pc.get() != final_pc:
    print("Error in run() tests: pc = {:#x}".format(pc.get()))
    sys.exit(1)

print("run() tests ran OK")
