# Helper module for Mit tests.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.enums import MitErrorCode
from mit.binding import uword_max, sign_bit


def cast_to_word(n):
    '''Truncate int to a signed word_bytes-sized quantity.'''
    return ((n + sign_bit) & uword_max) - sign_bit

def run_test(name, state, correct):
    '''
     - name - str - the name of the test (for error reporting).
     - state - State
     - correct - list of list of int - expected stack contents before each
       non-NEXT instruction.
    '''
    previous_ir = None
    done = 0
    def test_callback(handler, stack):
        '''Passed as `step_callback` to `State.step()`.'''
        nonlocal previous_ir, done
        # Check results before each instruction unless the previous one was NEXT.
        skip = previous_ir in (0, -1)
        previous_ir = handler.state.ir
        if skip:
            return
        correct_stack = list(map(cast_to_word, correct[done]))
        handler.log(f"Data stack: {stack}")
        handler.log(f"Correct stack: {correct_stack}\n")
        if correct_stack != list(stack):
            handler.log(f"Error in {name} tests: pc = {handler.state.pc:#x}")
            sys.exit(1)
        done += 1
        if done == len(correct):
            return MitErrorCode.BREAK
    state.step(trace=True, addr=0, step_callback=test_callback)
    print(f"{name.capitalize()} tests ran OK")
