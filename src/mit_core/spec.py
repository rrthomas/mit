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

from .autonumber import AutoNumber
from .params import word_bytes
from .code_util import Code
from .instruction import InstructionEnum
from .instruction_gen import dispatch
from .stack import StackEffect, pop_stack, push_stack


# Global constants (see module params for build-time parameters)
word_bit = word_bytes * 8
opcode_bit = 8

class RegisterEnum(AutoNumber):
    def __init__(self, type='mit_uword'):
        self.type = type

@unique
class Register(RegisterEnum):
    '''VM registers.'''
    pc = ('mit_word *')
    ir = ()
    stack_depth = ()
    stack = ('mit_word * restrict',)
    stack_words = ()

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


@unique
class Instruction(InstructionEnum):
    '''VM instructions.'''

    EXTRA = (
        None,
        Code(), # Code is computed below.
        0x0,
        True,
    )

    JUMP = (
        StackEffect.of(['addr'], []),
        Code('''\
            S->pc = (mit_word *)addr;
            CHECK_ALIGNED(S->pc);
            DO_NEXT;'''
        ),
        0x1,
        True,
    )

    JUMPZ = (
        StackEffect.of(['flag', 'addr'], []),
        Code('''\
            if (flag == 0) {
                S->pc = (mit_word *)addr;
                CHECK_ALIGNED(S->pc);
                DO_NEXT;
            }
        '''),
        0x2,
    )

    CALL = (
        StackEffect.of(['addr'], ['ret_addr']),
        Code('''\
            ret_addr = (mit_uword)S->pc;
            S->pc = (mit_word *)addr;
            CHECK_ALIGNED(S->pc);
            DO_NEXT;'''
        ),
        0x3,
        True,
    )

    POP = (
        StackEffect.of(['ITEMS', 'COUNT'], []),
        Code(), # No code.
        0x4,
    )

    DUP = (
        StackEffect.of(['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x']),
        Code(), # No code.
        0x5,
    )

    SWAP = (
        StackEffect.of(['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x']),
        Code(),
        0x6,
    )

    TRAP = (
        None,
        Code('''\
            {
                mit_word inner_error = mit_trap(S);
                if (inner_error != MIT_ERROR_OK)
                    RAISE(inner_error);
            }
        '''),
        0x7,
    )

    LOAD = (
        StackEffect.of(['addr'], ['val']),
        Code('''\
            if (unlikely(!is_aligned(addr, MIT_WORD_BYTES)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            val = *(mit_word *)addr;'''
        ),
        0x8,
    )

    STORE = (
        StackEffect.of(['val', 'addr'], []),
        Code('''\
            if (unlikely(!is_aligned(addr, MIT_WORD_BYTES)))
                RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
            *(mit_word *)addr = val;'''
        ),
        0x9,
    )

    LOAD1 = (
        StackEffect.of(['addr'], ['val']),
        Code('val = (mit_uword)*((uint8_t *)addr);'),
        0xa,
    )

    STORE1 = (
        StackEffect.of(['val', 'addr'], []),
        Code('*(uint8_t *)addr = (uint8_t)val;'),
        0xb,
    )

    LOAD2 = (
        StackEffect.of(['addr'], ['val']),
        Code('''\
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wcast-align"
                if (unlikely(!is_aligned(addr, 2)))
                    RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
                val = (mit_uword)*((uint16_t *)((uint8_t *)addr));
            #pragma GCC diagnostic pop'''
        ),
        0xc,
    )

    STORE2 = (
        StackEffect.of(['val', 'addr'], []),
        Code('''\
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wcast-align"
                if (unlikely(!is_aligned(addr, 2)))
                    RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
                *(uint16_t *)addr = (uint16_t)val;
            #pragma GCC diagnostic pop'''
        ),
        0xd,
    )

    LOAD4 = (
        StackEffect.of(['addr'], ['val']),
        Code('''\
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wcast-align"
                if (unlikely(!is_aligned(addr, 4)))
                    RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
                val = (mit_uword)*((uint32_t *)((uint8_t *)addr));
            #pragma GCC diagnostic pop'''
        ),
        0xe,
    )

    STORE4 = (
        StackEffect.of(['val', 'addr'], []),
        Code('''\
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wcast-align"
                if (unlikely(!is_aligned(addr, 4)))
                    RAISE(MIT_ERROR_UNALIGNED_ADDRESS);
                *(uint32_t *)addr = (uint32_t)val;
            #pragma GCC diagnostic pop'''
        ),
        0xf,
    )

    PUSH = (
        StackEffect.of([], ['n']),
        Code('n = *S->pc++;'),
        0x10,
    )

    PUSHREL = (
        StackEffect.of([], ['n']),
        Code('''\
            n = (mit_uword)S->pc;
            n += *S->pc++;
        '''),
        0x11,
    )

    NOT = (
        StackEffect.of(['x'], ['r']),
        Code('r = ~x;'),
        0x12,
    )

    AND = (
        StackEffect.of(['x', 'y'], ['r']),
        Code('r = x & y;'),
        0x13,
    )

    OR = (
        StackEffect.of(['x', 'y'], ['r']),
        Code('r = x | y;'),
        0x14,
    )

    XOR = (
        StackEffect.of(['x', 'y'], ['r']),
        Code('r = x ^ y;'),
        0x15,
    )

    LT = (
        StackEffect.of(['a', 'b'], ['flag']),
        Code('flag = a < b;'),
        0x16,
    )

    ULT = (
        StackEffect.of(['a', 'b'], ['flag']),
        Code('flag = (mit_uword)a < (mit_uword)b;'),
        0x17,
    )

    LSHIFT = (
        StackEffect.of(['x', 'n'], ['r']),
        Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x << n) : 0;'''
        ),
        0x18,
    )

    RSHIFT = (
        StackEffect.of(['x', 'n'], ['r']),
        Code('''\
            r = n < (mit_word)MIT_WORD_BIT ?
                (mit_word)((mit_uword)x >> n) : 0;'''
        ),
        0x19,
    )

    ARSHIFT = (
        StackEffect.of(['x', 'n'], ['r']),
        Code('r = ARSHIFT(x, n);'),
        0x1a,
    )

    NEGATE = (
        StackEffect.of(['a'], ['r']),
        Code('r = -a;'),
        0x1b,
    )

    ADD = (
        StackEffect.of(['a', 'b'], ['r']),
        Code('r = a + b;'),
        0x1c,
    )

    MUL = (
        StackEffect.of(['a', 'b'], ['r']),
        Code('r = a * b;'),
        0x1d,
    )

    DIVMOD = (
        StackEffect.of(['a', 'b'], ['q', 'r']),
        Code('''\
            if (b == 0)
                RAISE(MIT_ERROR_DIVISION_BY_ZERO);
            q = a / b;
            r = a % b;'''
        ),
        0x1e,
    )

    UDIVMOD = (
        StackEffect.of(['a', 'b'], ['q', 'r']),
        Code('''\
            if (b == 0)
                RAISE(MIT_ERROR_DIVISION_BY_ZERO);
            q = (mit_word)((mit_uword)a / (mit_uword)b);
            r = (mit_word)((mit_uword)a % (mit_uword)b);'''
        ),
        0x1f,
    )


# Generate code for ExtraInstruction.HALT
halt_code = Code()
halt_code.append('mit_word n;')
halt_code.extend(pop_stack('n'))
halt_code.append('RAISE(n);')

@unique
class ExtraInstruction(InstructionEnum):
    '''VM extra instructions.'''

    NEXT = (
        StackEffect.of([], []),
        Code('DO_NEXT;'),
        0x0,
    )

    # FIXME: improve code generation so the stack effects of the following can
    # be specified
    HALT = (
        None,
        halt_code,
        0x1,
    )

    SIZEOF_STATE = (
        StackEffect.of([], ['size']),
        Code('size = sizeof(mit_state);'),
        0x2,
    )

    THIS_STATE = (
        StackEffect.of([], ['this_state:mit_state *']),
        Code('this_state = S;'),
        0x3,
    )

    GET_PC = (
        None,
        Code(), # Code is computed below.
        0x4,
    )

    SET_PC = (
        None,
        Code(), # Code is computed below.
        0x5,
    )

    GET_IR = (
        None,
        Code(), # Code is computed below.
        0x6,
    )

    SET_IR = (
        None,
        Code(), # Code is computed below.
        0x7,
    )

    GET_STACK_DEPTH = (
        None,
        Code(), # Code is computed below.
        0x8,
    )

    SET_STACK_DEPTH = (
        None,
        Code(), # Code is computed below.
        0x9,
    )

    GET_STACK = (
        None,
        Code(), # Code is computed below.
        0xa,
    )

    SET_STACK = (
        None,
        Code(), # Code is computed below.
        0xb,
    )

    GET_STACK_WORDS = (
        None,
        Code(), # Code is computed below.
        0xc,
    )

    SET_STACK_WORDS = (
        None,
        Code(), # Code is computed below.
        0xd,
    )

    LOAD_STACK = (
        StackEffect.of(['pos', 'inner_state:mit_state *'], ['value', 'ret']),
        Code('''\
           value = 0;
           ret = mit_load_stack(inner_state, pos, &value);
        '''),
        0xe,
    )

    STORE_STACK = (
        StackEffect.of(['value', 'pos', 'inner_state:mit_state *'], ['ret']),
        Code('ret = mit_store_stack(inner_state, pos, value);'),
        0xf,
    )

    POP_STACK = (
        StackEffect.of(['inner_state:mit_state *'], ['value', 'ret']),
        Code('''\
            value = 0;
            ret = mit_pop_stack(inner_state, &value);
        '''),
        0x10,
    )

    PUSH_STACK = (
        StackEffect.of(['value', 'inner_state:mit_state *'], ['ret']),
        Code('ret = mit_push_stack(inner_state, value);'),
        0x11,
    )

    RUN = (
        StackEffect.of(['inner_state:mit_state *'], ['ret']),
        Code('ret = mit_run(inner_state);'),
        0x12,
    )

    SINGLE_STEP = (
        StackEffect.of(['inner_state:mit_state *'], ['ret']),
        Code('ret = mit_single_step(inner_state);'),
        0x13,
    )

    ARGC = (
        StackEffect.of([], ['argc']),
        Code('argc = (mit_word)mit_argc;'),
        0x100,
    )

    ARGV = (
        StackEffect.of([], ['argv:char **']),
        Code('argv = mit_argv;'),
        0x101,
    )

for register in Register:
    pop_code = Code()
    pop_code.append('mit_state *inner_state;')
    pop_code.extend(pop_stack('inner_state', type='mit_state *'))

    get_code = Code()
    get_code.extend(pop_code)
    get_code.extend(push_stack(
        f'inner_state->{register.name}',
        type=register.type,
    ))
    ExtraInstruction[f'GET_{register.name.upper()}'].code = get_code

    set_code = Code()
    set_code.extend(pop_code)
    set_code.append(f'{register.type} value;')
    set_code.extend(pop_stack('value', register.type))
    set_code.append(f'inner_state->{register.name} = value;')
    ExtraInstruction[f'SET_{register.name.upper()}'].code = set_code


# Inject code for Instruction.EXTRA
extra_code = Code('''\
    mit_uword extra_opcode = S->ir;
    S->ir = 0;
'''
)
extra_code.extend(dispatch(ExtraInstruction, Code(
    'RAISE(MIT_ERROR_INVALID_OPCODE);',
), 'extra_opcode'))
Instruction.EXTRA.code = extra_code
