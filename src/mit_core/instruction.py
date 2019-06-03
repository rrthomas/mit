'''
Class for instructions.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from enum import Enum

from .code_util import Code


class InstructionEnum(Enum):
    '''
    VM instruction instruction descriptor.

     - opcode - int - opcode number
     - args, results - lists of str, acceptable to StackPicture.of().
       If both are `None`, then the instruction has an arbitrary stack
       effect.
     - code - Code.
     - terminal - bool - this instruction is terminal: I must be zero on
       entry.

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    Macros available to instructions (see run.h):

    RAISE(error): the code should RAISE any error before writing any state,
    so that if an error is raised, the state of the VM is not changed.

    CHECK_ALIGNED(addr): check a VM address is valid, raising an error if
    not.

    FETCH_PC(w): fetch the word at PC, assign it to `w`, and increment PC by
    a word.

    DO_NEXT: perform the action of NEXT.
    '''
    def __init__(self, opcode, args, results, code, terminal=False):
        self.opcode = opcode
        if args is None or results is None:
            assert args is None and results is None
        assert isinstance(code, Code)
        self.args = args
        self.results = results
        self.code = code
        self.terminal = terminal

    @property
    def value(self):
        return self.opcode
