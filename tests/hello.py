# Hello world demo/test.
#
# (c) SMite authors 2018-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Assemble test code

# Address in next line = instructions + word_size × literals
lit(libsmite.smite_align(7 + 4 * word_size))
lit(14)
lit(LIB_C_STDOUT)
ass(LIB_C)
lit(LIB_C_WRITE)
ass(LIB_C)
ass(HALT)

bytes(b"Hello, world!\n")


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
