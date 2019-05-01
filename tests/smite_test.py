# Helper module for SMite tests.
#
# (c) SMite authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import sys

from smite.assembler import Disassembler

def cast_to_word(stack):
    return [n if n <= (1 << word_bit) - 1 else smite_uword_maxfor n in stack]

def run_test(name, state, correct):
    for i, stack in enumerate(correct):
        stack = cast_to_word(stack)
        print(Disassembler(state).__next__())
        state.step()
        print("Data stack: {}".format(state.S))
        print("Correct stack: {}\n".format(stack))
        if str(stack) != str(state.S):
            print("Error in {} tests: PC = {:#x}".format(
                name,
                state.registers["PC"].get()
            ))
            sys.exit(1)

    print("{} tests ran OK".format(name.capitalize()))
