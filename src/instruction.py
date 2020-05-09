'''
Class for instructions.

Copyright (c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from dataclasses import dataclass

from action import Action
from code_util import Code


@dataclass
class Instruction(Action):
    '''
    VM instruction descriptor.

     - terminal_action - Action or None - if given, this instruction is
       terminal: the rest of `ir` is its argument, and the Action gives the
       implementation for the case when `ir` is non-zero.

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    There are special macros available to instructions; see run.h.
    '''
    terminal_action: Action

    def gen_case(self):
        code = super().gen_case()
        if self.terminal_action is not None:
            code = Code(
                'if (S->ir != 0) {',
                self.terminal_action.gen_case(),
                '} else {',
                code,
                '}',
            )
        return code
