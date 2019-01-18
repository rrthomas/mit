# Test the CALL_NATIVE instruction.
#
# (c) Reuben Thomas 1995-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from smite import *
VM = State()
VM.globalize(globals())


correct = 37

# Test callback
def test(state):
    S.push(correct)
test_func = SMITE_CALLBACK_FUNCTYPE(test)

# Test code
pointer(cast(test_func, c_void_p).value)
action(CALL_NATIVE)
number(0)
action(HALT)

# Test
res = run()
if res != 0:
    print("Error in CALL_NATIVE tests: test aborted with return code {}".format(res))
    sys.exit(1)

top_word = S.pop()
print("Top of stack is {}; should be {}".format(top_word, correct))
print("Data stack: {}".format(S))
if top_word != correct:
    print("Error in CALL_NATIVE tests: incorrect value on top of stack\n")
    sys.exit(1)

print("CALL_NATIVE tests ran OK")
