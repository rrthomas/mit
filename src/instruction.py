'''
Class for instructions.

Copyright (c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from enum import Enum

from code_util import Code
from stack import StackEffect


class InstructionEnum(Enum):
    '''
    VM instruction descriptor.

     - effect - StackEffect or None.
     - code - Code.
     - opcode - int or None - opcode number, defaults to the number of
       instructions before adding this one.
     - terminal - bool - this instruction is terminal: the rest of `ir` is its
       argument.
     - is_variadic - bool - true if this instruction is variadic.

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    There are special macros available to instructions; see run.h.
    '''
    def __new__(cls, *args):
        obj = object.__new__(cls)
        obj.opcode = len(cls.__members__)
        return obj

    def __init__(self, effect, code, opcode=None, terminal=False):
        '''
          - effect - tuple of two lists of str, acceptable to StackPicture.of(),
            or `None`, meaning that the instruction has an arbitrary stack
            effect.
        '''
        assert effect is None or isinstance(effect, StackEffect), effect
        self.effect = effect
        assert isinstance(code, Code), code
        self.code = code
        if opcode is not None:
            self.opcode = opcode
        self.terminal = terminal
        self.is_variadic = (
            self.effect is not None and
            any(item.name == 'ITEMS' for item in self.effect.args.items)
        )
