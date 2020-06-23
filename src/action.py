'''
Class for instruction actions.

Action represents an instruction's semantics, and is subclassed to add other
information such as its encoding.

Copyright (c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from dataclasses import dataclass
from enum import Enum

from code_util import Code
from stack import StackEffect


@dataclass
class Action:
    '''
    VM instruction action descriptor.

     - effect - StackEffect or None.
     - code - Code - may use macros defined in run.h. If `effect` is not
       `None`, `run_py.gen_action_case()` creates C variables for the
       arguments and results, pops the arguments and pushes the results;
       otherwise, `code` is responsible for managing the stack.
     - is_variadic - bool - true if this action is variadic.
    '''
    effect: StackEffect
    code: Code

    def __post_init__(self):
        self.is_variadic = (
            self.effect is not None and
            any(item.name == 'ITEMS' for item in self.effect.args.items)
        )

class ActionEnum(Enum):
    '''
    Base class for instruction-set–like enumerations.

     - action - Action or Instruction.
     - opcode - optional int - opcode number, defaults to numbering
       sequentially from 0.

    Typically, classes inherit from ActionEnum and add extra fields they
    require.
    '''
    def __new__(cls, *args):
        obj = object.__new__(cls)
        obj.opcode = len(cls.__members__)
        return obj

    def __init__(self, action, opcode=None):
        self.action = action
        if opcode is not None:
            self.opcode = opcode
