'''
Optimized versions of Instructions with strings attached.

Copyright (c) 2018-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''


from mit_core.code_buffer import Code
from mit_core.vm_data import Instruction
from mit_core.instruction import InstructionEnum


def _replace_items(picture, replacement):
    '''
    Replaces 'ITEMS' with `replacement` in `picture`
    '''
    ret = []
    for item in picture:
        if item == 'ITEMS':
            ret.extend(replacement)
        else:
            ret.append(item)
    return ret

def _gen_specialized_instruction(instruction, tos_constant):
    replacement = ['x{}'.format(i) for i in range(tos_constant)]
    code = Code()
    code.append('assert(COUNT == {});'.format(tos_constant))
    code.extend(instruction.code)
    return (
        instruction.opcode,
        _replace_items(instruction.args, replacement),
        _replace_items(instruction.results, replacement),
        code,
        instruction.terminal,
    )

SpecializedInstruction = InstructionEnum('SpecializedInstruction', {
    '{name}_WITH_{tos_constant}'.format(
        name=instruction.name,
        tos_constant=tos_constant,
    ): _gen_specialized_instruction(instruction, tos_constant)
    for instruction in Instruction
    if 'ITEMS' in instruction.args
    for tos_constant in range(4)
})

