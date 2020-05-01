'''
Specialized Instructions.

Copyright (c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from code_util import Code
from spec import Instruction, ExtraInstruction
from stack import StackEffect, Size
import instruction


class InstructionEnum(instruction.InstructionEnum):
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
    def __init__(self, guard, effect, code, opcode=None, terminal=False):
        super().__init__(effect, code, opcode, terminal)
        self.guard = guard
        assert not self.is_variadic
        if effect is not None:
            assert all(
                item.size == Size(1)
                for item in effect.by_name.values()
            ), instruction

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
        guard,
        instruction.effect,
        instruction.code,
        instruction.opcode,
        instruction.terminal,
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
    code.extend(instruction.code)
    return (
        f'{{stack_0}} == {count}',
        StackEffect.of(
            _replace_items(instruction.effect.args, replacement),
            _replace_items(instruction.effect.results, replacement),
        ),
        code,
        instruction.opcode,
        instruction.terminal,
    )

specialized_instructions = {}
for instruction in Instruction:
    if instruction.is_variadic:
        for count in range(4):
            specialized_instructions[f'{instruction.name}_WITH_{count}'] = \
                _gen_variadic_instruction(instruction, count)
    elif instruction.name == 'JUMPZ':
        specialized_instructions['JUMPZ_TAKEN'] = _gen_ordinary_instruction(
            instruction,
            '{stack_1} == 0',
        )
        specialized_instructions['JUMPZ_UNTAKEN'] = _gen_ordinary_instruction(
            instruction,
            '{stack_1} != 0',
        )
    elif instruction.effect is not None:
        specialized_instructions[instruction.name] = \
            _gen_ordinary_instruction(instruction)

Instruction = InstructionEnum(
    'Instruction',
    specialized_instructions,
)

# The set of Instructions that might modify the `ir` register.
# We cannot guess beyond such an instruction.
GUESS_LIMITING = frozenset([
    Instruction.NEXT,
    Instruction.JUMP,
    Instruction.JUMPZ_TAKEN,
    Instruction.CALL,
])
