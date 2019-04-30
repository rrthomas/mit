'''
Class for instructions.

Copyright (c) 2009-2019 SMite authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from enum import Enum

class AbstractInstruction(Enum):
    '''
    VM instruction instruction descriptor.

     - opcode - int - opcode number
     - effect - StackEffect (or None for arbitrary stack effect)
     - code - str - C source code

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    The code should RAISE any error before writing any state, so that if an
    error is raised, the state of the VM is not changed.
    '''
    def __init__(self, opcode, args, results, code):
        '''
         - args, results - lists of str, acceptable to StackPicture.of().
           If both are `None`, then the instruction has an arbitrary stack
           effect, like `EXT`.
        '''
        self.opcode = opcode
        if args is None or results is None:
            assert args is None and results is None
        self.args = args
        self.results = results
        self.code = code

    @classmethod
    def print(cls, prefix):
        '''Print the instructions as a C enum.'''
        print('\nenum {')
        for instruction in cls:
            print("    INSTRUCTION({}{}, {:#x})".format(
                prefix,
                instruction.name,
                instruction.opcode,
            ))
        print('};')