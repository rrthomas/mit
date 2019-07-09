# VM definition
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, IntEnum, unique

from .code_util import Code
from .instruction import InstructionEnum
from .register import RegisterEnum


@unique
class Register(RegisterEnum):
    '''A VM register.'''
    pc = ()
    ir = ()
    bad = ()
    stack_depth = ()
    # Registers that are not part of the spec
    memory = ('mit_word *')
    memory_size = ()
    stack = ('mit_word * restrict')
    stack_size = ()

@unique
class MitErrorCode(IntEnum):
    OK = 0
    INVALID_OPCODE = 1
    STACK_OVERFLOW = 2
    INVALID_STACK_READ = 3
    INVALID_STACK_WRITE = 4
    INVALID_MEMORY_READ = 5
    INVALID_MEMORY_WRITE = 6
    UNALIGNED_ADDRESS = 7
    BAD_SIZE = 8
    DIVISION_BY_ZERO = 9
    HALT = 127

@unique
class Instruction(InstructionEnum):
    '''VM instruction instructions.'''
    NEXT = (0x0, [], [], Code('''\
        DO_NEXT;'''
    ), True)

    JUMP = (0x1, ['addr'], [], Code('''\
        S->pc = (mit_uword)addr;
        CHECK_ALIGNED(S->pc);
        DO_NEXT;'''
    ), True)

    JUMPZ = (0x2, ['flag', 'addr'], [], Code('''\
        if (flag == 0) {
            S->pc = (mit_uword)addr;
            CHECK_ALIGNED(S->pc);
            DO_NEXT;
        }
    '''))

    CALL = (0x3, ['addr'], ['ret_addr'], Code('''\
        ret_addr = S->pc;
        S->pc = (mit_uword)addr;
        CHECK_ALIGNED(S->pc);
        DO_NEXT;'''
    ), True)

    POP = (0x4, ['ITEMS', 'COUNT'], [], Code())

    DUP = (0x5, ['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x'], Code())

    SWAP = (0x6, ['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x'], Code())

    PUSH_STACK_DEPTH = (0x7, [], ['n'], Code('''\
        n = S->stack_depth;'''
    ))

    LOAD = (0x8, ['addr', 'size'], ['x'], Code('''\
        int ret = load(S->memory, S->memory_size, addr, size, &x);
        if (ret != 0) {
            S->bad = addr;
            RAISE(ret);
        }'''
    ))

    STORE = (0x9, ['x', 'addr', 'size'], [], Code('''\
        int ret = store(S->memory, S->memory_size, addr, size, x);
        if (ret != 0) {
            S->bad = addr;
            RAISE(ret);
        }'''
    ))

    LIT = (0xa, [], ['n'], Code('''\
        FETCH_PC(n);'''
    ))

    LIT_PC_REL = (0xb, [], ['n'], Code('''\
        FETCH_PC(n);
        n += S->pc - MIT_WORD_BYTES;'''
    ))

    LIT_0 = (0xc, [], ['zero'], Code('''\
        zero = 0;'''
    ))

    LIT_1 = (0xd, [], ['one'], Code('''\
        one = 1;'''
    ))

    LIT_2 = (0xe, [], ['two'], Code('''\
        two = 2;'''
    ))

    LIT_3 = (0xf, [], ['three'], Code('''\
        three = 3;'''
    ))

    LT = (0x11, ['a', 'b'], ['flag'], Code('''\
        flag = a < b;'''
    ))

    ULT = (0x12, ['a', 'b'], ['flag'], Code('''\
        flag = (mit_uword)a < (mit_uword)b;'''
    ))

    NEGATE = (0x13, ['a'], ['r'], Code('''\
        r = -a;'''
    ))

    ADD = (0x14, ['a', 'b'], ['r'], Code('''\
        r = a + b;'''
    ))

    MUL = (0x15, ['a', 'b'], ['r'], Code('''\
        r = a * b;'''
    ))

    DIVMOD = (0x16, ['a', 'b'], ['q', 'r'], Code('''\
        if (b == 0)
          RAISE(MIT_ERROR_DIVISION_BY_ZERO);
        q = a / b;
        r = a % b;'''
    ))

    UDIVMOD = (0x17, ['a', 'b'], ['q', 'r'], Code('''\
        if (b == 0)
          RAISE(MIT_ERROR_DIVISION_BY_ZERO);
        q = (mit_word)((mit_uword)a / (mit_uword)b);
        r = (mit_word)((mit_uword)a % (mit_uword)b);'''
    ))

    NOT = (0x18, ['x'], ['r'], Code('''\
        r = ~x;'''
    ))

    AND = (0x19, ['x', 'y'], ['r'], Code('''\
        r = x & y;'''
    ))

    OR = (0x1a, ['x', 'y'], ['r'], Code('''\
        r = x | y;'''
    ))

    XOR = (0x1b, ['x', 'y'], ['r'], Code('''\
        r = x ^ y;'''
    ))

    LSHIFT = (0x1c, ['x', 'n'], ['r'], Code('''\
        r = n < (mit_word)MIT_WORD_BIT ? x << n : 0;'''
    ))

    RSHIFT = (0x1d, ['x', 'n'], ['r'], Code('''\
        r = n < (mit_word)MIT_WORD_BIT ? (mit_word)((mit_uword)x >> n) : 0;'''
    ))

    ARSHIFT = (0x1e, ['x', 'n'], ['r'], Code('''\
        r = ARSHIFT(x, n);'''
    ))

    SIGN_EXTEND = (0x1f, ['n1', 'size'], ['n2'], Code('''\
        n2 = n1 << (MIT_WORD_BYTES - (1 << size)) * MIT_BYTE_BIT;
        n2 = ARSHIFT(n2, (MIT_WORD_BYTES - (1 << size)) * MIT_BYTE_BIT);'''
    ))

@unique
class InternalExtraInstruction(InstructionEnum):
    HALT = (0x1, [], [], Code('''\
        RAISE(MIT_ERROR_HALT);'''
    ))
