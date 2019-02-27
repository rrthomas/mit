# Test that the VM headers compile properly, and that the
# storage allocation and register initialisation in storage.c works.
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *

size = 1024
VM = State(size // word_size, 1)
if VM == None:
    print("Error in init() tests: init with valid parameters failed")
    sys.exit(1)

print("init() tests ran OK")
