# Helper module for Mit tests.
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from mit.assembler import Disassembler
from mit.binding import word_bit, uword_max

def cast_to_word(stack):
    return [n if 0 <= n < (1 << (word_bit - 1)) else
            ((n | ~uword_max) if n > -uword_max else 0)
            for n in stack]

def run_test(name, state, correct):
    for i, stack in enumerate(correct):
        stack = cast_to_word(stack)
        print(Disassembler(state).__next__())
        state.step()
        print("Data stack: {}".format(state.S))
        print("Correct stack: {}\n".format(stack))
        if str(stack) != str(state.S):
            print("Error in {} tests: pc = {:#x}".format(
                name,
                state.registers["pc"].get()
            ))
            sys.exit(1)

    print("{} tests ran OK".format(name.capitalize()))
