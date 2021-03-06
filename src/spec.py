# VM definition
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from dataclasses import dataclass
from enum import Enum, IntEnum, unique
from ctypes import sizeof, c_size_t

from autonumber import AutoNumber
from stack import StackEffect
from action import Action, ActionEnum
from code_util import Code
from code_gen import dispatch


word_bytes = sizeof(c_size_t)
word_bit = word_bytes * 8
opcode_bit = 8

class RegisterEnum(AutoNumber):
    def __init__(self, type):
        self.type = type

@unique
class Registers(RegisterEnum):
    '''VM registers.'''
    pc = ('mit_word_t *',)
    ir = ('mit_word_t',)

@unique
class MitErrorCode(IntEnum):
    '''VM error codes.'''
    OK = 0
    INVALID_OPCODE = -1
    INVALID_THROW = -2
    STACK_OVERFLOW = -3
    INVALID_STACK_READ = -4
    INVALID_STACK_WRITE = -5
    INVALID_MEMORY_READ = -6
    INVALID_MEMORY_WRITE = -7
    UNALIGNED_ADDRESS = -8
    DIVISION_BY_ZERO = -9
    DIVISION_OVERFLOW = -10
    BREAK = -126


@unique
class ExtraInstructions(ActionEnum):
    '''VM extra instructions.'''
    DIVMOD = (
        Action(
            StackEffect.of(['a', 'b'], ['q', 'r']),
            Code('''\
                if (b == 0)
                    THROW(MIT_ERROR_DIVISION_BY_ZERO);
                q = a / b;
                r = a % b;
            ''')
        ),
        0x1,
    )

    UDIVMOD = (
        Action(
            StackEffect.of(['a', 'b'], ['q', 'r']),
            Code('''\
                if (b == 0)
                    THROW(MIT_ERROR_DIVISION_BY_ZERO);
                q = (mit_word_t)((mit_uword_t)a / (mit_uword_t)b);
                r = (mit_word_t)((mit_uword_t)a % (mit_uword_t)b);
            ''')
        ),
        0x2,
    )

    THROW = (
        Action(
            None, # Manage stack manually so that `stack_depth` is
                  # decremented before THROW().
            Code('''\
                POP(n);
                THROW(n);
            '''),
        ),
        0x3,
    )

    CATCH = (
        Action(
            None, # Manage stack manually because the stack module doesn't
                  # understand multiple stack frames.
            Code('''\
                POP(addr);
                if (unlikely(addr % sizeof(mit_word_t) != 0))
                   THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                DO_CATCH(addr);
            '''),
        ),
        0x4,
    )

    ARGC = (
        Action(
            StackEffect.of([], ['argc']),
            Code('argc = (mit_word_t)mit_argc;'),
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
    mit_uword_t extra_opcode = ir;
    ir = 0;
''')
extra_code.extend(dispatch(
    ExtraInstructions,
    Code(
        'THROW(MIT_ERROR_INVALID_OPCODE);',
    ),
    'extra_opcode',
))


# Core instructions.
@dataclass
class Instruction:
    '''
    VM instruction descriptor.

     - opcode - int - the instruction's opcode.
     - action - Action
     - terminal - Action or None - if given, this instruction is
       terminal, and its action depends on the rest of `ir`. If all bits of
       `ir` match the top bit of `opcode`, the action is `action`,
       otherwise it is `terminal`.
    '''
    opcode: int
    action: Action
    terminal: Action

instructions = [
    {
        'name': 'NEXT',
        'opcode': 0x00,
        'action': Action(
            StackEffect.of([], []),
            Code('DO_NEXT;'),
        ),
        'terminal': Action(
            None,
            extra_code, # Computed above.
        ),
    },

    {
        'name': 'NOT',
        'opcode': 0x01,
        'action': Action(
            StackEffect.of(['x'], ['r']),
            Code('r = ~x;'),
        ),
    },

    {
        'name': 'AND',
        'opcode': 0x02,
        'action': Action(
            StackEffect.of(['x', 'y'], ['r']),
            Code('r = x & y;'),
        ),
    },

    {
        'name': 'OR',
        'opcode': 0x03,
        'action': Action(
            StackEffect.of(['x', 'y'], ['r']),
            Code('r = x | y;'),
        ),
    },

    {
        'name': 'XOR',
        'opcode': 0x04,
        'action': Action(
            StackEffect.of(['x', 'y'], ['r']),
            Code('r = x ^ y;'),
        ),
    },

    {
        'name': 'LSHIFT',
        'opcode': 0x05,
        'action': Action(
            StackEffect.of(['x', 'n'], ['r']),
            Code('''\
                r = n < (mit_word_t)MIT_WORD_BIT ?
                    (mit_word_t)((mit_uword_t)x << n) : 0;
            '''),
        ),
    },

    {
        'name': 'RSHIFT',
        'opcode': 0x06,
        'action': Action(
            StackEffect.of(['x', 'n'], ['r']),
            Code('''\
                r = n < (mit_word_t)MIT_WORD_BIT ?
                    (mit_word_t)((mit_uword_t)x >> n) : 0;
            '''),
        ),
    },

    {
        'name': 'ARSHIFT',
        'opcode': 0x07,
        'action': Action(
            StackEffect.of(['x', 'n'], ['r']),
            Code('r = ARSHIFT(x, n);'),
        ),
    },

    {
        'name': 'POP',
        'opcode': 0x08,
        'action': Action(
            StackEffect.of(['_x'], []),
            Code('(void)_x;'),
        ),
    },

    {
        'name': 'DUP',
        'opcode': 0x09,
        'action': Action(
            StackEffect.of(['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x']),
            Code(), # No code.
        ),
    },

    {
        'name': 'SET',
        'opcode': 0x0a,
        'action': Action(
            StackEffect.of(['_x_count', 'ITEMS', 'x0', 'COUNT'], ['x0', 'ITEMS']),
            Code('(void)_x_count;'),
        ),
    },

    {
        'name': 'SWAP',
        'opcode': 0x0b,
        'action': Action(
            StackEffect.of(['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x']),
            Code(),
        ),
    },

    {
        'name': 'JUMP',
        'opcode': 0x0c,
        'action': Action(
            StackEffect.of(['addr'], []),
            Code('DO_JUMP(addr);'),
        ),
        'terminal': Action(
            StackEffect.of([], []),
            Code('DO_JUMPI;'),
        ),
    },

    {
        'name': 'JUMPZ',
        'opcode': 0x0d,
        'action': Action(
            StackEffect.of(['flag', 'addr'], []),
            Code('''\
                if (flag == 0)
                    DO_JUMP(addr);
            '''),
        ),
        'terminal': Action(
            StackEffect.of(['flag'], []),
            Code('''\
                if (flag == 0)
                    DO_JUMPI;
            '''),
        ),
    },

    {
        'name': 'CALL',
        'opcode': 0x0e,
        'action': Action(
            None, # Manage stack manually because of changing stack frames.
            Code('''\
                POP(addr);
                if (unlikely(addr % sizeof(mit_word_t) != 0))
                   THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                DO_CALL(addr);
            '''),
        ),
        'terminal': Action(
            None, # Manage stack manually because of changing stack frames.
            Code('''\
                mit_word_t addr = (mit_uword_t)(pc + ir);
                DO_CALL(addr);
            '''),
        ),
    },

    {
        'name': 'RET',
        'opcode': 0x0f,
        'action': Action(
            None,
            # `call` or `catch` performs the rest of the action of `ret` on
            # return from `run_inner()`.
            Code('return;'),
        ),
    },

    {
        'name': 'LOAD',
        'opcode': 0x10,
        'action': Action(
            StackEffect.of(['addr'], ['val']),
            Code('''\
                if (unlikely(addr % sizeof(mit_word_t) != 0))
                    THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                val = *(mit_word_t *)addr;
            '''),
        ),
    },

    {
        'name': 'STORE',
        'opcode': 0x11,
        'action': Action(
            StackEffect.of(['val', 'addr'], []),
            Code('''\
                if (unlikely(addr % sizeof(mit_word_t) != 0))
                    THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                *(mit_word_t *)addr = val;
            '''),
        ),
    },

    {
        'name': 'LOAD1',
        'opcode': 0x12,
        'action': Action(
            StackEffect.of(['addr'], ['val']),
            Code('val = (mit_uword_t)*((uint8_t *)addr);'),
        ),
    },

    {
        'name': 'STORE1',
        'opcode': 0x13,
        'action': Action(
            StackEffect.of(['val', 'addr'], []),
            Code('*(uint8_t *)addr = (uint8_t)val;'),
        ),
    },

    {
        'name': 'LOAD2',
        'opcode': 0x14,
        'action': Action(
            StackEffect.of(['addr'], ['val']),
            Code('''\
                if (unlikely(addr % 2 != 0))
                    THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                val = (mit_uword_t)*((uint16_t *)addr);
            '''),
        ),
    },

    {
        'name': 'STORE2',
        'opcode': 0x15,
        'action': Action(
            StackEffect.of(['val', 'addr'], []),
            Code('''\
                if (unlikely(addr % 2 != 0))
                    THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                *(uint16_t *)addr = (uint16_t)val;
            '''),
        ),
    },

    {
        'name': 'LOAD4',
        'opcode': 0x16,
        'action': Action(
            StackEffect.of(['addr'], ['val']),
            Code('''\
                if (unlikely(addr % 4 != 0))
                    THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                val = (mit_uword_t)*((uint32_t *)addr);
            '''),
        ),
    },

    {
        'name': 'STORE4',
        'opcode': 0x17,
        'action': Action(
            StackEffect.of(['val', 'addr'], []),
            Code('''\
                if (unlikely(addr % 4 != 0))
                    THROW(MIT_ERROR_UNALIGNED_ADDRESS);
                *(uint32_t *)addr = (uint32_t)val;
            '''),
        ),
    },

    {
        'name': 'PUSH',
        'opcode': 0x18,
        'action': Action(
            StackEffect.of([], ['val']),
            Code('val = *pc++;'),
        ),
    },

    {
        'name': 'PUSHREL',
        'opcode': 0x19,
        'action': Action(
            StackEffect.of([], ['addr']),
            Code('''\
                addr = (mit_uword_t)pc + *pc;
                pc++;
            '''),
        ),
    },

    {
        'name': 'NEG',
        'opcode': 0x1a,
        'action': Action(
            StackEffect.of(['a'], ['b']),
            Code('b = -(mit_uword_t)a;'),
        ),
    },

    {
        'name': 'ADD',
        'opcode': 0x1b,
        'action': Action(
            StackEffect.of(['a', 'b'], ['c']),
            Code('c = (mit_uword_t)a + (mit_uword_t)b;'),
        ),
    },

    {
        'name': 'MUL',
        'opcode': 0x1c,
        'action': Action(
            StackEffect.of(['a', 'b'], ['c']),
            Code('c = (mit_uword_t)a * (mit_uword_t)b;'),
        ),
    },

    {
        'name': 'EQ',
        'opcode': 0x1d,
        'action': Action(
            StackEffect.of(['a', 'b'], ['flag']),
            Code('flag = a == b;'),
        ),
    },

    {
        'name': 'LT',
        'opcode': 0x1e,
        'action': Action(
            StackEffect.of(['a', 'b'], ['flag']),
            Code('flag = a < b;'),
        ),
    },

    {
        'name': 'ULT',
        'opcode': 0x1f,
        'action': Action(
            StackEffect.of(['a', 'b'], ['flag']),
            Code('flag = (mit_uword_t)a < (mit_uword_t)b;'),
        ),
    },
]
# Compute the final opcodes
for i in instructions:
    i['opcode'] <<= 3

# `trap`/`nextff`
instructions.extend([
    {
        'name': 'NEXTFF',
        'opcode': 0xff,
        'action': Action(
            StackEffect.of([], []),
            Code('DO_NEXT;'),
        ),
        'terminal': Action(
            None,
            Code('''\
                {
                    mit_word_t inner_error = mit_trap(pc, ir, stack, stack_words, &stack_depth);
                    if (inner_error != MIT_ERROR_OK)
                        THROW(inner_error);
                }
            '''),
        ),
    }
])

# `pushi`
instructions.extend(
    {
        'name': f'PUSHI_{n}'.replace('-', 'M'),
        'opcode': ((n & 0x1f) << 3) | (0x3 if n >= 0 else 0x4),
        'action': Action(
            StackEffect.of([], ['n']),
            Code(f'n = {n};'),
        ),
    }
    for n in range(-32, 32)
)

# `pushreli`
instructions.extend(
    {
        'name': f'PUSHRELI_{n}'.replace('-', 'M'),
        'opcode': ((n & 0x3f) << 2) | (0x1 if n >= 0 else 0x2),
        'action': Action(
            StackEffect.of([], ['addr']),
            Code(f'addr = (mit_uword_t)(pc + {n});'),
        ),
    }
    for n in range(-64, 64)
)


# Full instruction enumeration.
Instructions = unique(ActionEnum(
    'Instructions',
    ((
        i['name'],
        (
            Instruction(i['opcode'], i['action'], i.get('terminal', None)),
            i['opcode'],
        )
    ) for i in instructions)
))
Instructions.__doc__ = 'VM instructions.'
