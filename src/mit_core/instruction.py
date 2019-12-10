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
     - effect - StackEffect or None.
     - code - Code.
     - terminal - bool - this instruction is terminal: `ir` must be zero on
       entry.

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    There are special macros available to instructions; see run.h.
    '''
    def __init__(self, opcode, effect, code, terminal=False):
        '''
          - effect - tuple of two lists of str, acceptable to StackPicture.of(),
            or `None`, meaning that the instruction has an arbitrary stack
            effect.
        '''
        self.opcode = opcode
        if effect is None:
            self.effect = None
        else:
            assert type(effect) is tuple and len(effect) == 2
            self.effect = StackEffect(StackPicture.of(effect[0]),
                                      StackPicture.of(effect[1]))
        assert isinstance(code, Code)
        self.code = code
        self.terminal = terminal
        self.is_variadic = (
            self.effect is not None and
            any(item.name == 'ITEMS' for item in self.effect.args.items)
        )
