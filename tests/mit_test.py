# Helper module for Mit tests.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.enums import MitErrorCode, Instructions
from mit.binding import uword_max, sign_bit


def cast_to_word(n):
    return ((n + sign_bit) & uword_max) - sign_bit

def run_test(name, state, correct):
    ir = None
    done = 0
    def test_callback(handler, stack):
        nonlocal correct, ir, done
        # Check results after each non-NEXT instruction.
        previous_ir = ir
        ir = handler.state.ir
        if previous_ir in (None, 0, -1):
            return
        correct_stack = list(map(cast_to_word, correct[done]))
        print(f"Data stack: {stack}")
        print(f"Correct stack: {correct_stack}\n")
        if correct_stack != list(stack):
            print(f"Error in {name} tests: pc = {handler.state.pc:#x}")
            sys.exit(1)
        done += 1
        if done == len(correct):
            return MitErrorCode.OK
    state.step(trace=True, addr=0, step_callback=test_callback)
    print(f"{name.capitalize()} tests ran OK")
