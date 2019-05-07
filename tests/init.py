# Test that the VM headers compile properly, and that the
# storage allocation and register initialisation in storage.c works.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit import *

size = 1024
VM = State(size // word_bytes, 1)
if VM == None:
    print("Error in init() tests: init with valid parameters failed")
    sys.exit(1)

print("init() tests ran OK")
