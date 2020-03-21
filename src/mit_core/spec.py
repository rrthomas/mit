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
from .stack import StackEffect


with open(os.path.join(os.path.dirname(__file__), 'mit_spec.yaml')) as f:
    spec = yaml.safe_load(f.read())


class RegisterEnum(AutoNumber):
    def __init__(self, type='mit_uword'):
        self.type = type

register = {r: () for r in spec['Register']}
register['memory'] = ('mit_word *',)
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
                StackEffect.of(i['args'], i['results']),
                code[name],
                i['opcode'],
                i.get('terminal', False),
            ),
        ) for name, i in spec.items())
    ))
    enum.__doc__ = docstring
    return enum

Instruction = instruction_enum(
    'Instruction',
    'VM instruction opcodes.',
    spec['Instruction'],
    {
        'NEXT': Code('DO_NEXT;'),

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

        'PUSH_STACK_DEPTH': Code('n = S->stack_depth;'),

        'LOAD': Code('''\
            int ret = load(addr, size, &x);
            if (ret != 0)
                RAISE(ret);'''
        ),

        'STORE': Code('''\
            int ret = store(addr, size, x);
            if (ret != 0)
                RAISE(ret);'''
        ),

        'LIT': Code('FETCH_PC(n);'),

        'LIT_PC_REL': Code('''\
            FETCH_PC(n);
            n += S->pc - MIT_WORD_BYTES;'''
        ),

        'LIT_0': Code(),
        'LIT_1': Code(),
        'LIT_2': Code(),
        'LIT_3': Code(),

        'LT': Code('flag = a < b;'),
        'ULT': Code('flag = (mit_uword)a < (mit_uword)b;'),

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

        'NOT': Code('r = ~x;'),
        'AND': Code('r = x & y;'),
        'OR': Code('r = x | y;'),
        'XOR': Code('r = x ^ y;'),

        'LSHIFT': Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x << n) : 0;'''
        ),
        'RSHIFT': Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x >> n) : 0;'''
        ),
        'ARSHIFT': Code('r = ARSHIFT(x, n);'),

        'SIGN_EXTEND': Code('''\
            n = u << (MIT_WORD_BYTES - (1 << size)) * MIT_BYTE_BIT;
            n = ARSHIFT(n, (MIT_WORD_BYTES - (1 << size)) * MIT_BYTE_BIT);'''
        ),
    },
)

InternalExtraInstruction = instruction_enum(
    'InternalExtraInstruction',
    'Internal extra instruction opcodes.',
    spec['InternalExtraInstruction'],
    {
        'HALT': Code('RAISE(MIT_ERROR_HALT);'),
    },
)
