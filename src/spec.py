# VM definition
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

import os
from dataclasses import dataclass
from enum import Enum, IntEnum, unique

from autonumber import AutoNumber
from params import word_bytes
from code_util import Code
from action import Action, ActionEnum
from stack import StackEffect, pop_stack, push_stack


# Global constants (see module params for build-time parameters)
word_bit = word_bytes * 8
opcode_bit = 8

class RegisterEnum(AutoNumber):
    def __init__(self, type='mit_uword'):
        self.type = type

@unique
class Registers(RegisterEnum):
    '''VM registers.'''
    pc = ('mit_word *',)
    ir = ('mit_word',)
    stack_depth = ()
    stack = ('mit_word * restrict',)

@unique
class MitErrorCode(IntEnum):
    '''VM error codes.'''
    OK = 0
    INVALID_OPCODE = -1
    STACK_OVERFLOW = -2
    INVALID_STACK_READ = -3
    INVALID_STACK_WRITE = -4
    INVALID_MEMORY_READ = -5
    INVALID_MEMORY_WRITE = -6
    UNALIGNED_ADDRESS = -7
    DIVISION_BY_ZERO = -8
    BREAK = -127


# Core instructions.
@dataclass
class Instruction(Action):
    '''
    VM instruction descriptor.

     - opcode - int - the instruction's opcode.
     - terminal_action - Action or None - if given, this instruction is
       terminal: the rest of `ir` is its argument, and the Action gives the
       implementation for the case when `ir` is not zero (if the opcode's
       top bit is clear) or -1 (if it is set).

    C variables are created for the arguments and results; the arguments are
    popped and results pushed.

    There are special macros available to instructions; see run.h.
    '''
    opcode: int
    terminal_action: Action

    def gen_case(self):
        code = super().gen_case()
        if self.terminal_action is not None:
            ir_all_bits = 0 if self.opcode & 0x80 == 0 else -1
            code = Code(
                f'if (ir != {ir_all_bits}) {{',
                self.terminal_action.gen_case(),
                '} else {',
                code,
                '}',
            )
        return code

instructions = [
    {
        'name': 'NEXT',
        'effect': StackEffect.of([], []),
        'code': Code('DO_NEXT;'),
        'opcode': 0x0,
        'terminal': Action(
            None,
            Code(), # Computed below.
        ),
    },

    {
        'name': 'NEXTFF',
        'effect': StackEffect.of([], []),
        'code': Code('DO_NEXT;'),
        'opcode': 0xff,
        'terminal': Action(
            None,
            Code('''\
                {
                    mit_word inner_error = mit_trap(ir, stack, &stack_depth);
                    if (inner_error != MIT_ERROR_OK)
                        RAISE(inner_error);
                }
            '''),
        ),
    },

    {
        'name': 'POP',
        'effect': StackEffect.of(['ITEMS', 'COUNT'], []),
        'code': Code(), # No code.
        'opcode': 0x1,
    },

    {
        'name': 'DUP',
        'effect': StackEffect.of(['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x']),
        'code': Code(), # No code.
        'opcode': 0x2,
    },

    {
        'name': 'SWAP',
        'effect': StackEffect.of(['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x']),
        'code': Code(),
        'opcode': 0x3,
    },

    {
        'name': 'JUMP',
        'effect': StackEffect.of(['addr'], []),
        'code': Code('DO_JUMP;'),
        'opcode': 0x4,
        'terminal': Action(
            StackEffect.of([], []),
            Code('DO_JUMPI;'),
        ),
    },

    {
        'name': 'JUMPZ',
        'effect': StackEffect.of(['flag', 'addr'], []),
        'code': Code('''\
            if (flag == 0)
                DO_JUMP;'''),
        'opcode': 0x5,
        'terminal': Action(
            StackEffect.of(['flag'], []),
            Code('''\
                if (flag == 0)
                    DO_JUMPI;'''),
        ),
    },

    {
        'name': 'CALL',
        'effect': None,
        'code': Code('''\
            POP(addr);
            if (unlikely(addr % MIT_WORD_BYTES != 0))
               RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            DO_CALL(addr);
        '''),
        'opcode': 0x6,
        'terminal': Action(
            None,
            Code('''\
                mit_word addr = (mit_uword)(pc + ir);
                DO_CALL(addr);
        '''),
        ),
    },

    {
        'name': 'RET',
        'effect': None,
        'code': Code('''\
            memcpy(outer_stack, stack + stack_depth - nres, nres * MIT_WORD_BYTES);
            // For `RET_ERROR`, see run_fn.py.
            return RET_ERROR; // `call` sets `pc` and `ir` on return from `run_inner()`.
        '''),
        'opcode': 0x7,
    },

    {
        'name': 'LOAD',
        'effect': StackEffect.of(['addr'], ['val']),
        'code': Code('''\
            if (unlikely(addr % MIT_WORD_BYTES != 0))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = *(mit_word *)addr;
        '''),
        'opcode': 0x8,
    },

    {
        'name': 'STORE',
        'effect': StackEffect.of(['val', 'addr'], []),
        'code': Code('''\
            if (unlikely(addr % MIT_WORD_BYTES != 0))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(mit_word *)addr = val;
        '''),
        'opcode': 0x9,
    },

    {
        'name': 'LOAD1',
        'effect': StackEffect.of(['addr'], ['val']),
        'code': Code('val = (mit_uword)*((uint8_t *)addr);'),
        'opcode': 0xa,
    },

    {
        'name': 'STORE1',
        'effect': StackEffect.of(['val', 'addr'], []),
        'code': Code('*(uint8_t *)addr = (uint8_t)val;'),
        'opcode': 0xb,
    },

    {
        'name': 'LOAD2',
        'effect': StackEffect.of(['addr'], ['val']),
        'code': Code('''\
            if (unlikely(addr % 2 != 0))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = (mit_uword)*((uint16_t *)addr);
        '''),
        'opcode': 0xc,
    },

    {
        'name': 'STORE2',
        'effect': StackEffect.of(['val', 'addr'], []),
        'code': Code('''\
            if (unlikely(addr % 2 != 0))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(uint16_t *)addr = (uint16_t)val;
        '''),
        'opcode': 0xd,
    },

    {
        'name': 'LOAD4',
        'effect': StackEffect.of(['addr'], ['val']),
        'code': Code('''\
            if (unlikely(addr % 4 != 0))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = (mit_uword)*((uint32_t *)addr);
        '''),
        'opcode': 0xe,
    },

    {
        'name': 'STORE4',
        'effect': StackEffect.of(['val', 'addr'], []),
        'code': Code('''\
            if (unlikely(addr % 4 != 0))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(uint32_t *)addr = (uint32_t)val;
        '''),
        'opcode': 0xf,
    },

    {
        'name': 'PUSH',
        'effect': StackEffect.of([], ['n']),
        'code': Code('n = *pc++;'),
        'opcode': 0x10,
    },

    {
        'name': 'PUSHREL',
        'effect': StackEffect.of([], ['n']),
        'code': Code('''\
            n = (mit_uword)pc;
            n += *pc++;
        '''),
        'opcode': 0x11,
    },

    {
        'name': 'NOT',
        'effect': StackEffect.of(['x'], ['r']),
        'code': Code('r = ~x;'),
        'opcode': 0x12,
    },

    {
        'name': 'AND',
        'effect': StackEffect.of(['x', 'y'], ['r']),
        'code': Code('r = x & y;'),
        'opcode': 0x13,
    },

    {
        'name': 'OR',
        'effect': StackEffect.of(['x', 'y'], ['r']),
        'code': Code('r = x | y;'),
        'opcode': 0x14,
    },

    {
        'name': 'XOR',
        'effect': StackEffect.of(['x', 'y'], ['r']),
        'code': Code('r = x ^ y;'),
        'opcode': 0x15,
    },

    {
        'name': 'LT',
        'effect': StackEffect.of(['a', 'b'], ['flag']),
        'code': Code('flag = a < b;'),
        'opcode': 0x16,
    },

    {
        'name': 'ULT',
        'effect': StackEffect.of(['a', 'b'], ['flag']),
        'code': Code('flag = (mit_uword)a < (mit_uword)b;'),
        'opcode': 0x17,
    },

    {
        'name': 'LSHIFT',
        'effect': StackEffect.of(['x', 'n'], ['r']),
        'code': Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x << n) : 0;
        '''),
        'opcode': 0x18,
    },

    {
        'name': 'RSHIFT',
        'effect': StackEffect.of(['x', 'n'], ['r']),
        'code': Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x >> n) : 0;
        '''),
        'opcode': 0x19,
    },

    {
        'name': 'ARSHIFT',
        'effect': StackEffect.of(['x', 'n'], ['r']),
        'code': Code('r = ARSHIFT(x, n);'),
        'opcode': 0x1a,
    },

    {
        'name': 'NEGATE',
        'effect': StackEffect.of(['a'], ['r']),
        'code': Code('r = -a;'),
        'opcode': 0x1b,
    },

    {
        'name': 'ADD',
        'effect': StackEffect.of(['a', 'b'], ['r']),
        'code': Code('r = a + b;'),
        'opcode': 0x1c,
    },

    {
        'name': 'MUL',
        'effect': StackEffect.of(['a', 'b'], ['r']),
        'code': Code('r = a * b;'),
        'opcode': 0x1d,
    },

    {
        'name': 'DIVMOD',
        'effect': StackEffect.of(['a', 'b'], ['q', 'r']),
        'code': Code('''\
            if (b == 0)
                RAISE(MIT_ERROR_DIVISION_BY_ZERO);
            q = a / b;
            r = a % b;
        '''),
        'opcode': 0x1e,
    },

    {
        'name': 'UDIVMOD',
        'effect': StackEffect.of(['a', 'b'], ['q', 'r']),
        'code': Code('''\
            if (b == 0)
                RAISE(MIT_ERROR_DIVISION_BY_ZERO);
            q = (mit_word)((mit_uword)a / (mit_uword)b);
            r = (mit_word)((mit_uword)a % (mit_uword)b);
        '''),
        'opcode': 0x1f,
    },
]

# Turn instruction codes into full opcodes
for i in instructions:
    if i['opcode'] != 0xff:
        i['opcode'] <<= 2


# `pushi`
instructions.extend([
    {
        'name': f'PUSHI_{n}'.replace('-', 'M'),
        'effect': StackEffect.of([], ['n']),
        'code': Code(f'n = {n};'),
        'opcode': ((n & 0x3f) << 2) | 0x2,
    }
    for n in range(-32, 32)
])

# `pushreli`
instructions.extend([
    {
        'name': f'PUSHRELI_{n}'.replace('-', 'M'),
        'effect': StackEffect.of([], ['addr']),
        'code': Code(f'addr = (mit_uword)(pc + {n});'),
        'opcode': ((n & 0x7f) << 1) | 0x1,
    }
    for n in range(-64, 64) if n != -1
])


# Full instruction enumeration.
Instructions = unique(ActionEnum(
    'Instructions',
    ((
        i['name'],
        (
            Instruction(i['effect'], i['code'], i['opcode'], i.get('terminal', None)),
            i['opcode'],
        )
    ) for i in instructions)
))
Instructions.__docstring__ = 'VM instructions.'


@unique
class ExtraInstructions(ActionEnum):
    '''VM extra instructions.'''

    # FIXME: improve code generation so the stack effect can be specified.
    HALT = (
        Action(
            None,
            Code('mit_word n;', str(pop_stack('n')), 'RAISE(n);'),
        ),
        0x1,
    )

    # FIXME: Must take arguments and returns, like CALL. CATCH?
    RUN = (
        Action(
            StackEffect.of(['inner_pc:mit_word *'], ['ret']),
            Code('ret = mit_run(inner_pc);'),
        ),
        0x11,
    )

    ARGC = (
        Action(
            StackEffect.of([], ['argc']),
            Code('argc = (mit_word)mit_argc;'),
        ),
        0x100,
    )

    ARGV = (
        Action(
            StackEffect.of([], ['argv:char **']),
            Code('argv = mit_argv;'),
        ),
        0x101,
    )

# Inject code for EXTRA
extra_code = Code('''\
    mit_uword extra_opcode = ir;
    ir = 0;
''')
extra_code.extend(ExtraInstructions.dispatch(Code(
    'RAISE(MIT_ERROR_INVALID_OPCODE);',
), 'extra_opcode'))
Instructions.NEXT.action.terminal_action.code = extra_code
