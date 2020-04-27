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

# Address in next line = instructions + word_bytes × literals
code_len = 0
# Hack: two-pass assembly to calculate code_len
for i in range(2):
    goto(M.addr)
    lit(code_len)
    lit(14)
    lit(LibC.STDOUT)
    lit(LIBC)
    ass(TRAP)
    lit(LibC.WRITE)
    lit(LIBC)
    ass(TRAP)
    lit(MitErrorCode.OK)
    ass(EXTRA, HALT)
    code_len = assembler.pc

ass_bytes(b"Hello, world!\n")


# Test
import sys
import io
import re

from redirect_stdout import stdout_redirector

f = io.BytesIO()
with stdout_redirector(f):
    run()
output = f.getvalue()
correct_file = re.sub(".py$", ".correct", sys.argv[0])
correct = open(correct_file, "rb").read()

print("Output:\n{}\n\nCorrect:\n{}".format(output,correct))
assert(output == correct)
