# VM definition
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import os
from enum import Enum, IntEnum, unique

import yaml

from .autonumber import AutoNumber
from .code_util import Code
from .instruction import InstructionEnum
from .instruction_gen import dispatch
from .stack import StackEffect, pop_stack, push_stack


with open(os.path.join(os.path.dirname(__file__), 'mit_spec.yaml')) as f:
    spec = yaml.safe_load(f.read())


class RegisterEnum(AutoNumber):
    def __init__(self, type='mit_uword'):
        self.type = type

register = {r: () for r in spec['Register']}
register['stack'] = ('mit_word * restrict',)
Register = unique(RegisterEnum('Register', register))
Register.__doc__ = 'VM registers.'

MitErrorCode = unique(IntEnum('MitErrorCode', spec['ErrorCode']))

def instruction_enum(enum_name, docstring, spec, code):
    enum = unique(InstructionEnum(
        enum_name,
        ((
            name,
            (
                StackEffect.of(i['args'], i['results']) if 'args' in i else None,
                code[name],
                i['opcode'],
                i.get('terminal', False),
            ),
        ) for name, i in spec.items())
    ))
    enum.__doc__ = docstring
    return enum

opcode_bit = 8

Instruction = instruction_enum(
    'Instruction',
    'VM instruction opcodes.',
    spec['Instruction'],
    {
        'EXTRA': Code(), # Code is computed later

        'JUMP': Code('''\
            S->pc = (mit_uword)addr;
            CHECK_ALIGNED(S->pc);
            DO_NEXT;'''
        ),

        'JUMPZ': Code('''\
            if (flag == 0) {
                S->pc = (mit_uword)addr;
                CHECK_ALIGNED(S->pc);
                DO_NEXT;
            }
        '''),

        'CALL': Code('''\
            ret_addr = S->pc;
            S->pc = (mit_uword)addr;
            CHECK_ALIGNED(S->pc);
            DO_NEXT;'''
        ),

        'POP': Code(),
        'DUP': Code(),
        'SWAP': Code(),

        'TRAP': Code('''\
            {
                mit_word inner_error = mit_trap(S);
                if (inner_error != MIT_ERROR_OK)
                    RAISE(inner_error);
            }
        '''),

        'LOAD': Code('''\
            if (unlikely(!is_aligned(addr, MIT_WORD_BYTES)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = *(mit_word *)addr;'''
        ),

        'STORE': Code('''\
            if (unlikely(!is_aligned(addr, MIT_WORD_BYTES)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(mit_word *)addr = val;'''
        ),

        'LOAD1': Code('val = (mit_uword)*((uint8_t *)addr);'),
        'STORE1': Code('*(uint8_t *)addr = (uint8_t)val;'),

        'LOAD2': Code('''\
        #pragma GCC diagnostic push
        #pragma GCC diagnostic ignored "-Wcast-align"
            if (unlikely(!is_aligned(addr, 2)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = (mit_uword)*((uint16_t *)((uint8_t *)addr));
        #pragma GCC diagnostic pop'''
        ),

        'STORE2': Code('''\
        #pragma GCC diagnostic push
        #pragma GCC diagnostic ignored "-Wcast-align"
            if (unlikely(!is_aligned(addr, 2)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(uint16_t *)addr = (uint16_t)val;
        #pragma GCC diagnostic pop'''
        ),

        'LOAD4': Code('''\
        #pragma GCC diagnostic push
        #pragma GCC diagnostic ignored "-Wcast-align"
            if (unlikely(!is_aligned(addr, 4)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = (mit_uword)*((uint32_t *)((uint8_t *)addr));
        #pragma GCC diagnostic pop'''
        ),

        'STORE4': Code('''\
        #pragma GCC diagnostic push
        #pragma GCC diagnostic ignored "-Wcast-align"
            if (unlikely(!is_aligned(addr, 4)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(uint32_t *)addr = (uint32_t)val;
        #pragma GCC diagnostic pop'''
        ),

        'PUSH': Code('FETCH_PC(n);'),

        'PUSHREL': Code('''\
            FETCH_PC(n);
            n += S->pc - MIT_WORD_BYTES;'''
        ),

        'NOT': Code('r = ~x;'),
        'AND': Code('r = x & y;'),
        'OR': Code('r = x | y;'),
        'XOR': Code('r = x ^ y;'),

        'LT': Code('flag = a < b;'),
        'ULT': Code('flag = (mit_uword)a < (mit_uword)b;'),

        'LSHIFT': Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x << n) : 0;'''
        ),
        'RSHIFT': Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x >> n) : 0;'''
        ),
        'ARSHIFT': Code('r = ARSHIFT(x, n);'),

        'NEGATE': Code('r = -a;'),
        'ADD': Code('r = a + b;'),
        'MUL': Code('r = a * b;'),

        'DIVMOD': Code('''\
            if (b == 0)
                RAISE(MIT_ERROR_DIVISION_BY_ZERO);
            q = a / b;
            r = a % b;'''
        ),

        'UDIVMOD': Code('''\
            if (b == 0)
                RAISE(MIT_ERROR_DIVISION_BY_ZERO);
            q = (mit_word)((mit_uword)a / (mit_uword)b);
            r = (mit_word)((mit_uword)a % (mit_uword)b);'''
        ),
    },
)

extra_instructions = {}

for register in Register:
    pop_code = Code()
    pop_code.append('mit_state *inner_state;')
    pop_code.extend(pop_stack('inner_state', type='mit_state *'))

    get_code = Code()
    get_code.extend(pop_code)
    get_code.extend(push_stack(
        'inner_state->{}'.format(register.name),
        type=register.type,
    ))
    extra_instructions['GET_{}'.format(register.name.upper())] = get_code

    set_code = Code()
    set_code.extend(pop_code)
    set_code.append('{} value;'.format(register.type))
    set_code.extend(pop_stack('value', register.type))
    set_code.append('''\
        inner_state->{} = value;'''.format(register.name),
    )
    extra_instructions['SET_{}'.format(register.name.upper())] = set_code

halt_code = Code()
halt_code.append('mit_word n;')
halt_code.extend(pop_stack('n'))
halt_code.append('RAISE(n);')
halt_code

extra_instructions.update({
    'NEXT': Code('DO_NEXT;'),

    'HALT': halt_code,

    'SIZEOF_STATE': Code('size = sizeof(mit_state);'),

    'THIS_STATE': Code('this_state = S;'),

    'LOAD_STACK': Code('''\
        value = 0;
        ret = mit_load_stack(inner_state, pos, &value);
    '''),

    'STORE_STACK': Code('ret = mit_store_stack(inner_state, pos, value);'),

    'POP_STACK': Code('''\
        value = 0;
        ret = mit_pop_stack(inner_state, &value);
    '''),

    'PUSH_STACK': Code('ret = mit_push_stack(inner_state, value);'),

    'RUN': Code('ret = mit_run(inner_state);'),

    'SINGLE_STEP': Code('ret = mit_single_step(inner_state);'),

    'ARGC': Code('argc = (mit_word)mit_argc;'),

    'ARGV': Code('argv = mit_argv;'),
})

ExtraInstruction = instruction_enum(
    'ExtraInstruction',
    'Extra instruction opcodes.',
    spec['ExtraInstruction'],
    extra_instructions,
)

# Inject code for EXTRA
extra_code = Code('''\
    mit_uword extra_opcode = S->ir;
    S->ir = 0;
'''
)
extra_code.extend(dispatch(ExtraInstruction, Code(
    'RAISE(MIT_ERROR_INVALID_OPCODE);',
), 'extra_opcode'))
Instruction.EXTRA.code = extra_code
