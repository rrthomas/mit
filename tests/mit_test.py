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
from mit.binding import word_mask, sign_bit


def cast_to_word(n):
    return ((n + sign_bit) & word_mask) - sign_bit

def run_test(name, state, correct):
    correct.insert(0, [])
    def test_callback(handler, stack):
        nonlocal correct
        correct_stack = list(map(cast_to_word, correct[handler.done]))
        print(f"Data stack: {stack}")
        print(f"Correct stack: {correct_stack}\n")
        if correct_stack != list(stack):
            print(f"Error in {name} tests: pc = {handler.state.pc:#x}")
            sys.exit(1)
    state.step(trace=True, n=len(correct), step_callback=test_callback)
    print(f"{name.capitalize()} tests ran OK")
