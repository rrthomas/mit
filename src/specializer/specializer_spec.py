'''
Specialized Instructions.

Copyright (c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from dataclasses import dataclass

from code_util import Code
from action import Action, ActionEnum
from spec import Instructions, ExtraInstructions
from stack import StackEffect, Size


@dataclass
class Instruction(Action):
    '''
    Specialized VM instruction descriptor.
    
     - guard - str - C expression which must evaluate to true for the
       specialized instruction to be executed. The guard may assume that the
       stack contains enough items to read `effect.args`.
     
    Specialized instructions have only one control flow path. Instructions with
    more than one control flow path are modelled as several specialized
    instructions with the same opcode and different guard expressions; the
    guards for a particular opcode must be exclusive.

    Specialized instructions cannot be variadic.
    '''
    guard: str
    terminal: bool=False

    def __post_init__(self):
        super().__post_init__()
        assert not self.is_variadic
        if self.effect is not None:
            assert all(
                item.size == Size(1)
                for item in self.effect.by_name.values()
            ), self

    def __repr__(self):
        return self.name


def _replace_items(picture, replacement):
    '''
    Replaces 'ITEMS' with `replacement` in `picture`
    '''
    ret = []
    for item in picture.items:
        if item.size.count != 0:
            ret.extend(replacement)
        else:
            ret.append(item.name)
    return ret

def _gen_ordinary_instruction(instruction, guard='1'):
    return (
        Instruction(
            instruction.action.effect,
            instruction.action.code,
            guard,
            instruction.action.terminal_action is not None,
        ),
        instruction.opcode,
    )

def _gen_variadic_instruction(instruction, count):
    replacement = [f'x{i}' for i in range(count)]
    code = Code()
    code.append(f'''\
        (void)COUNT; // Avoid a warning with -DNDEBUG
        assert(COUNT == {count});
    ''')
    if count > 0:
        code.append('// Suppress warnings about possibly unused variables.')
        for i in range(count):
            code.append(f'(void)x{i};')
    code.extend(instruction.action.code)
    return (
        Instruction(
            StackEffect.of(
                _replace_items(instruction.action.effect.args, replacement),
                _replace_items(instruction.action.effect.results, replacement),
            ),
            code,
            f'{{stack_0}} == {count}',
            instruction.action.terminal_action is not None,
        ),
        instruction.opcode,
    )

specialized_instructions = {}
for instruction in Instructions:
    if instruction.action.is_variadic:
        for count in range(4):
            specialized_instructions[f'{instruction.name}_WITH_{count}'] = \
                _gen_variadic_instruction(instruction, count)
    elif instruction.action.effect is not None:
        specialized_instructions[instruction.name] = \
            _gen_ordinary_instruction(instruction)

Instructions = ActionEnum(
    'Instructions',
    specialized_instructions,
)

# The set of Instructions that might modify the `ir` register.
# We cannot guess beyond such an instruction.
GUESS_LIMITING = frozenset([
    Instructions.NEXT,
    Instructions.JUMP,
    Instructions.JUMPZ,
    Instructions.CALL,
])
