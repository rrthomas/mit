# Helper module for Mit tests.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.assembler import Disassembler
from mit import word_bit, uword_max

def cast_to_word(stack):
    return [n if 0 <= n < (1 << (word_bit - 1)) else
            ((n | ~uword_max) if n > -uword_max else 0)
            for n in stack]

def run_test(name, state, correct):
    for i, stack in enumerate(correct):
        stack = cast_to_word(stack)
        print(Disassembler(state).__next__())
        state.trace()
        print(f"Data stack: {state.S}")
        print(f"Correct stack: {stack}\n")
        if stack != list(state.S):
            print(f"Error in {name} tests: pc = {state.pc:#x}")
            sys.exit(1)

    print(f"{name.capitalize()} tests ran OK")
