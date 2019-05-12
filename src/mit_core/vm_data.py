# VM definition
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique

from .instruction import AbstractInstruction


class AbstractRegister(Enum):
    @property
    def ty(self): return "mit_UWORD"

    @property
    def uty(self): return self.ty

    @property
    def read_only(self): return False

class Register(AbstractRegister):
    '''A VM register.'''
    PC = object()
    I = object()
    BAD = object()
    STACK_DEPTH = object()

@unique
class Instruction(AbstractInstruction):
    '''VM instruction instructions.'''
    NEXT = (0x00, [], [], '''\
        NEXT;'''
    )

    BRANCH = (0x01, ['addr'], [], '''\
        S->PC = (mit_UWORD)addr;
        NEXT;
    ''')

    BRANCHZ = (0x02, ['flag', 'addr'], [], '''\
        if (flag == 0) {
            S->PC = (mit_UWORD)addr;
            NEXT;
        }
    ''')

    CALL = (0x03, ['addr'], ['ret_addr'], '''\
        ret_addr = S->PC;
        S->PC = (mit_UWORD)addr;
        NEXT;
    ''')

    POP = (0x04, ['ITEMS', 'COUNT'], [], '')

    DUP = (0x05, ['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x'], '')

    SWAP = (0x06, ['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x'], '')

    PUSH_STACK_DEPTH = (0x07, [], ['n'], '''\
        n = S->STACK_DEPTH;
    ''')

    NOT = (0x08, ['x'], ['r'], '''\
        r = ~x;
    ''')

    AND = (0x09, ['x', 'y'], ['r'], '''\
        r = x & y;
    ''')

    OR = (0x0a, ['x', 'y'], ['r'], '''\
        r = x | y;
    ''')

    XOR = (0x0b, ['x', 'y'], ['r'], '''\
        r = x ^ y;
    ''')

    LSHIFT = (0x0c, ['x', 'n'], ['r'], '''\
        r = n < (mit_WORD)mit_WORD_BIT ? x << n : 0;
    ''')

    RSHIFT = (0x0d, ['x', 'n'], ['r'], '''\
        r = n < (mit_WORD)mit_WORD_BIT ? (mit_WORD)((mit_UWORD)x >> n) : 0;
    ''')

    ARSHIFT = (0x0e, ['x', 'n'], ['r'], '''\
        r = ARSHIFT(x, n);
    ''')

    SIGN_EXTEND = (0x0f, ['n1', 'size'], ['n2'], '''\
        n2 = n1 << (mit_WORD_BYTES - (1 << size)) * mit_BYTE_BIT;
        n2 = ARSHIFT(n2, (mit_WORD_BYTES - (1 << size)) * mit_BYTE_BIT);
    ''')

    EQ = (0x10, ['a', 'b'], ['flag'], '''\
        flag = a == b;
    ''')

    LT = (0x11, ['a', 'b'], ['flag'], '''\
        flag = a < b;
    ''')

    ULT = (0x12, ['a', 'b'], ['flag'], '''\
        flag = (mit_UWORD)a < (mit_UWORD)b;
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
          RAISE(MIT_ERR_DIVISION_BY_ZERO);
        q = a / b;
        r = a % b;
    ''')

    UDIVMOD = (0x17, ['a', 'b'], ['q', 'r'], '''\
        if (b == 0)
          RAISE(MIT_ERR_DIVISION_BY_ZERO);
        q = (mit_WORD)((mit_UWORD)a / (mit_UWORD)b);
        r = (mit_WORD)((mit_UWORD)a % (mit_UWORD)b);
    ''')

    LOAD = (0x18, ['addr', 'size'], ['x'], '''\
        int ret = load(S, addr, size, &x);
        if (ret != 0)
            RAISE(ret);
    ''')

    STORE = (0x19, ['x', 'addr', 'size'], [], '''\
        int ret = store(S, addr, size, x);
        if (ret != 0)
            RAISE(ret);
    ''')

    LIT = (0x1a, [], ['n'], '''\
        int ret = load(S, S->PC, mit_SIZE_WORD, &n);
        if (ret != 0)
            RAISE(ret);
        S->PC += mit_WORD_BYTES;
    ''')

    LIT_PC_REL = (0x1b, [], ['n'], '''\
        int ret = load(S, S->PC, mit_SIZE_WORD, &n);
        if (ret != 0)
            RAISE(ret);
        n += S->PC;
        S->PC += mit_WORD_BYTES;
    ''')

    LIT_0 = (0x1c, [], ['zero'], '''\
        zero = 0;
    ''')

    LIT_1 = (0x1d, [], ['one'], '''\
        one = 1;
    ''')

    HALT = (0x1f, [], [], '''\
        RAISE(MIT_ERR_HALT);
    ''')
