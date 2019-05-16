# VM definition
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, IntEnum, unique

from .instruction import AbstractInstruction


class Register(Enum):
    '''A VM register.'''
    PC = object()
    I = object()
    BAD = object()
    STACK_DEPTH = object()

@unique
class ExecutionError(IntEnum):
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
    HALT = 128

@unique
class Instruction(AbstractInstruction):
    '''VM instruction instructions.'''
    NEXT = (0x0, [], [], '''\
        NEXT;'''
    )

    BRANCH = (0x1, ['addr'], [], '''\
        S->PC = (mit_uword)addr;
        NEXT;
    ''',
              '''\
        if (S->I != 0)
            RAISE(MIT_ERROR_INVALID_OPCODE);
    ''')

    BRANCHZ = (0x2, ['flag', 'addr'], [], '''\
        if (flag == 0) {
            S->PC = (mit_uword)addr;
            NEXT;
        }
    ''')

    CALL = (0x3, ['addr'], ['ret_addr'], '''\
        ret_addr = S->PC;
        S->PC = (mit_uword)addr;
        NEXT;
    ''',
            '''\
        if (S->I != 0) {
            mit_word ret = mit_internal_extra_instruction(S);
            if (ret != 0)
                RAISE(ret);
        }
    ''')

    POP = (0x4, ['ITEMS', 'COUNT'], [], '')

    DUP = (0x5, ['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x'], '')

    SWAP = (0x6, ['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x'], '')

    PUSH_STACK_DEPTH = (0x7, [], ['n'], '''\
        n = S->STACK_DEPTH;
    ''')

    LOAD = (0x8, ['addr', 'size'], ['x'], '''\
        int ret = load(S, addr, size, &x);
        if (ret != 0)
            RAISE(ret);
    ''')

    STORE = (0x9, ['x', 'addr', 'size'], [], '''\
        int ret = store(S, addr, size, x);
        if (ret != 0)
            RAISE(ret);
    ''')

    LIT = (0xa, [], ['n'], '''\
        int ret = load(S, S->PC, MIT_SIZE_WORD, &n);
        if (ret != 0)
            RAISE(ret);
        S->PC += MIT_WORD_BYTES;
    ''')

    LIT_PC_REL = (0xb, [], ['n'], '''\
        int ret = load(S, S->PC, MIT_SIZE_WORD, &n);
        if (ret != 0)
            RAISE(ret);
        n += S->PC;
        S->PC += MIT_WORD_BYTES;
    ''')

    LIT_0 = (0xc, [], ['zero'], '''\
        zero = 0;
    ''')

    LIT_1 = (0xd, [], ['one'], '''\
        one = 1;
    ''')

    LIT_2 = (0xe, [], ['two'], '''\
        two = 2;
    ''')

    LIT_3 = (0xf, [], ['three'], '''\
        three = 3;
    ''')

    EQ = (0x10, ['a', 'b'], ['flag'], '''\
        flag = a == b;
    ''')

    LT = (0x11, ['a', 'b'], ['flag'], '''\
        flag = a < b;
    ''')

    ULT = (0x12, ['a', 'b'], ['flag'], '''\
        flag = (mit_uword)a < (mit_uword)b;
    ''')

    NEGATE = (0x13, ['a'], ['r'], '''\
        r = -a;
    ''')

    ADD = (0x14, ['a', 'b'], ['r'], '''\
        r = a + b;
    ''')

    MUL = (0x15, ['a', 'b'], ['r'], '''\
        r = a * b;
    ''')

    DIVMOD = (0x16, ['a', 'b'], ['q', 'r'], '''\
        if (b == 0)
          RAISE(MIT_ERROR_DIVISION_BY_ZERO);
        q = a / b;
        r = a % b;
    ''')

    UDIVMOD = (0x17, ['a', 'b'], ['q', 'r'], '''\
        if (b == 0)
          RAISE(MIT_ERROR_DIVISION_BY_ZERO);
        q = (mit_word)((mit_uword)a / (mit_uword)b);
        r = (mit_word)((mit_uword)a % (mit_uword)b);
    ''')

    NOT = (0x18, ['x'], ['r'], '''\
        r = ~x;
    ''')

    AND = (0x19, ['x', 'y'], ['r'], '''\
        r = x & y;
    ''')

    OR = (0x1a, ['x', 'y'], ['r'], '''\
        r = x | y;
    ''')

    XOR = (0x1b, ['x', 'y'], ['r'], '''\
        r = x ^ y;
    ''')

    LSHIFT = (0x1c, ['x', 'n'], ['r'], '''\
        r = n < (mit_word)MIT_WORD_BIT ? x << n : 0;
    ''')

    RSHIFT = (0x1d, ['x', 'n'], ['r'], '''\
        r = n < (mit_word)MIT_WORD_BIT ? (mit_word)((mit_uword)x >> n) : 0;
    ''')

    ARSHIFT = (0x1e, ['x', 'n'], ['r'], '''\
        r = ARSHIFT(x, n);
    ''')

    SIGN_EXTEND = (0x1f, ['n1', 'size'], ['n2'], '''\
        n2 = n1 << (MIT_WORD_BYTES - (1 << size)) * MIT_BYTE_BIT;
        n2 = ARSHIFT(n2, (MIT_WORD_BYTES - (1 << size)) * MIT_BYTE_BIT);
    ''')

@unique
class InternalExtraInstruction(AbstractInstruction):
    HALT = (0x1, [], [], '''\
        RAISE(MIT_ERROR_HALT);
    ''')
