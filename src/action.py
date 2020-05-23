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

from code_util import Code, c_symbol
from stack import StackEffect, Size, check_underflow, check_overflow


@dataclass
class Action:
    '''
    VM instruction action descriptor.

     - effect - StackEffect or None.
     - code - Code.
     - is_variadic - bool - true if this action is variadic.
    '''
    effect: StackEffect
    code: Code

    def __post_init__(self):
        self.is_variadic = (
            self.effect is not None and
            any(item.name == 'ITEMS' for item in self.effect.args.items)
        )

    def gen_case(self):
        '''
        Generate a Code for an Action.

        In the code, errors are reported by calling THROW().
        '''
        effect = self.effect
        code = Code()
        if effect is not None:
            # Load the arguments into C variables.
            code.extend(effect.declare_vars())
            count = effect.args.by_name.get('COUNT')
            if count is not None:
                # If we have COUNT, check its stack position is valid, and load it.
                # We actually check `effect.args.size.size` (more than we need),
                # because this check will be generated anyway by the next
                # check_underflow call, so the compiler can elide one check.
                code.extend(check_underflow(Size(effect.args.size.size)))
                code.extend(count.load())
            code.extend(check_underflow(effect.args.size))
            code.extend(check_overflow(effect.args.size, effect.results.size))
            code.extend(effect.load_args())
        code.extend(self.code)
        if effect is not None:
            # Store the results from C variables.
            code.append(f'stack_depth += {effect.results.size - effect.args.size};')
            code.extend(effect.store_results())
        return code

class ActionEnum(Enum):
    '''
    Base class for instruction-set–like enumerations.

     - action - Action
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
        assert isinstance(action, Action), action
        self.action = action
        if opcode is not None:
            self.opcode = opcode

    @classmethod
    def dispatch(cls, undefined_case, opcode='opcode'):
        '''
        Generate dispatch code.

         - undefined_case - Code - the fallback behaviour.
         - opcode - str - a C expression for the opcode.
        '''
        assert isinstance(undefined_case, Code), undefined_case
        code = Code()
        else_text = ''
        for (_, value) in enumerate(cls):
            code.append(
                f'{else_text}if ({opcode} == {c_symbol(cls.__name__)}_{value.name}) {{'
            )
            code.append(value.action.gen_case())
            code.append('}')
            else_text = 'else '
        code.append(f'{else_text}{{')
        code.append(undefined_case)
        code.append('}')
        return code
