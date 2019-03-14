# Hello world demo/test.
#
# (c) Reuben Thomas 2018
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


# Assemble test code

# here = 0
number(7)
number(14)

# here = 2
number(LIB_C_STDOUT)
action(LIB_C)

# here = 4
number(LIB_C_WRITE)
action(LIB_C)

# here = 6
action(HALT)

# here = 7
byte(0x48)
byte(0x65)
byte(0x6c)
byte(0x6c)
byte(0x6f)
byte(0x2c)
byte(0x20)
byte(0x77)
byte(0x6f)
byte(0x72)
byte(0x6c)
byte(0x64)
byte(0x21)
byte(0x0a)


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
