'''
Generate code for instructions.

Copyright (c) 2009-2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

The main entry point is dispatch().
'''

from code_util import Code, c_symbol
from instruction import InstructionEnum
from stack import Size, check_underflow, check_overflow


def gen_case(instruction):
    '''
    Generate a Code for an Instruction.

    In the code, S is the mit_state, and errors are reported by calling
    RAISE().

     - instruction - Instruction.
    '''
    effect = instruction.effect
    code = Code()
    if instruction.terminal and instruction.name != 'EXTRA':
        code.append(
            'if (unlikely(S->ir != 0)) RAISE(MIT_ERROR_INVALID_OPCODE);'
        )
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
    code.extend(instruction.code)
    if effect is not None:
        # Store the results from C variables.
        code.append(f'S->stack_depth += {effect.results.size - effect.args.size};')
        code.extend(effect.store_results())
    return code

def dispatch(instructions, undefined_case, opcode='opcode'):
    '''
    Generate dispatch code for some Instructions.

     - instructions - InstructionEnum.
     - undefined_case - Code - the fallback behaviour.
     - opcode - str - a C expression for the opcode.
    '''
    assert issubclass(instructions, InstructionEnum)
    assert isinstance(undefined_case, Code)
    code = Code()
    else_text = ''
    for (_, instruction) in enumerate(instructions):
        code.append(
            f'{else_text}if ({opcode} == {c_symbol(instructions.__name__)}_{instruction.name}) {{'
        )
        code.append(gen_case(instruction))
        code.append('}')
        else_text = 'else '
    code.append(f'{else_text}{{')
    code.append(undefined_case)
    code.append('}')
    return code
