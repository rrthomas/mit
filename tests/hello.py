# Hello world demo/test.
#
# (c) Mit authors 2018-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from mit.globals import *


# Assemble test code

text_addr = 0
# Hack: two-pass assembly to calculate code_len
for i in range(2):
    goto(M.addr)
    # Ensure the same length code is generated on each pass
    lit(text_addr, force_long=True)
    lit(14)
    lit(LibC.STDOUT)
    trap(LIBC)
    lit(LibC.WRITE)
    trap(LIBC)
    lit(MitErrorCode.OK)
    extra(THROW)
    text_addr = assembler.pc

ass_bytes(b"Hello, world!\n")


# Test
import sys, io, re

from redirect_stdout import stdout_redirector

f = io.BytesIO()
with stdout_redirector(f):
    run()
output = f.getvalue()
correct_file = re.sub(".py$", ".correct", sys.argv[0])
correct = open(correct_file, "rb").read()

print(f"Output:\n{output}\n\nCorrect:\n{correct}")
assert(output == correct)
