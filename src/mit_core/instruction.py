'''
Class for instructions.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from enum import Enum

from .code_util import Code
from .stack import StackPicture, StackEffect


class InstructionEnum(Enum):
    '''
    VM instruction instruction descriptor.

     - opcode - int - opcode number.
     - args, results - StackPicture.
     - effect - StackEffect or None.
     - code - Code.
     - terminal - bool - this instruction is terminal: `ir` must be zero on
       entry.

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    There are special macros available to instructions; see run.h.
    '''
    def __init__(self, opcode, args, results, code, terminal=False):
        '''
          - args, results - lists of str, acceptable to StackPicture.of().
            If both are `None`, then the instruction has an arbitrary stack
            effect.
        '''
        self.opcode = opcode
        if args is None or results is None:
            assert args is None and results is None
            self.args = None
            self.results = None
            self.effect = None
        else:
            self.args = StackPicture.of(args)
            self.results = StackPicture.of(results)
            self.effect = StackEffect(self.args, self.results)
        assert isinstance(code, Code)
        self.code = code
        self.terminal = terminal
        self.is_variadic = (
            self.args is not None and
            any(item.name == 'ITEMS' for item in self.args.items)
        )