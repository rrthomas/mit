'''
Specialized Instructions.

Copyright (c) 2019-2020 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from mit_core.code_util import Code
from mit_core.spec import Instruction
from mit_core.stack import StackEffect
from mit_core.instruction import InstructionEnum


class SpecializedInstructionEnum(InstructionEnum):
    '''
    Specialized VM instruction descriptor.
    
     - guard - str - C expression which must evaluate to true for the
       specialized instruction to be executed. The guard may assume that the
       stack contains enough items to read `effect.args`.
     
    Specialized instructions have only one control flow path. Instructions with
    more than one control flow path are modelled as several specialized
    instructions with the same opcode and different guard expressions; the
    guards for a particular opcode must be exclusive.
    '''
    def __init__(self, opcode, guard, effect, code, terminal=False):
        super().__init__(opcode, effect, code, terminal)
        self.guard = guard

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
        instruction.opcode,
        guard,
        instruction.effect,
        instruction.code,
        instruction.terminal,
    )

def _gen_variadic_instruction(instruction, count):
    replacement = ['x{}'.format(i) for i in range(count)]
    code = Code()
    code.append('assert(COUNT == {});'.format(count))
    if count > 0:
        code.append('// Suppress warnings about possibly unused variables.')
        for i in range(count):
            code.append('(void)x{};'.format(i))
    code.extend(instruction.code)
    return (
        instruction.opcode,
        '{{stack_0}} == {}'.format(count),
        StackEffect.of(
            _replace_items(instruction.effect.args, replacement),
            _replace_items(instruction.effect.results, replacement),
        ),
        code,
        instruction.terminal,
    )

specialized_instructions = {}
for instruction in Instruction:
    if instruction.is_variadic:
        for count in range(4):
            specialized_instructions['{name}_WITH_{count}'.format(
                name=instruction.name,
                count=count,
            )] = _gen_variadic_instruction(instruction, count)
    elif instruction.name in ('LOAD', 'STORE', 'SIGN_EXTEND'):
        for size in range(4):
            specialized_instructions['{name}_WITH_{size}'.format(
                name=instruction.name,
                size=size,
            )] = _gen_ordinary_instruction(
                instruction,
                '{{stack_0}} == {}'.format(size),
            )
    elif instruction.name == 'JUMPZ':
        specialized_instructions['JUMPZ_TAKEN'] = _gen_ordinary_instruction(
            instruction,
            '{{stack_1}} == 0',
        )
        specialized_instructions['JUMPZ_UNTAKEN'] = _gen_ordinary_instruction(
            instruction,
            '{{stack_1}} != 0',
        )
    else:
        specialized_instructions[instruction.name] = \
            _gen_ordinary_instruction(instruction)

SpecializedInstruction = SpecializedInstructionEnum(
    'SpecializedInstruction',
    specialized_instructions,
)
