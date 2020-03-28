# Test that storage allocation and register initialisation works.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.state import State

VM = State(1)
if VM is None:
    print("Error in init() tests: init with valid parameters failed")
    sys.exit(1)

print("init() tests ran OK")
