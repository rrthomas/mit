# VM definition
#
# (c) SMite authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique, auto

from .instruction import AbstractInstruction


class AbstractRegister(Enum):
    @property
    def ty(self): return "smite_UWORD"

    @property
    def uty(self): return self.ty

    @property
    def read_only(self): return False

class Register(AbstractRegister):
    '''A VM register.'''
    PC = auto()
    I = auto()
    BAD = auto()
    STACK_DEPTH = auto()

@unique
class Instruction(AbstractInstruction):
    '''VM instruction instructions.'''
    NEXT = (0x00, [], [], '''\
        NEXT;'''
    )

    BRANCH = (0x01, ['addr'], [], '''\
        S->PC = (smite_UWORD)addr;
        NEXT;
    ''')

    BRANCHZ = (0x02, ['flag', 'addr'], [], '''\
        if (flag == 0) {
            S->PC = (smite_UWORD)addr;
            NEXT;
        }
    ''')

    CALL = (0x03, ['addr'], ['ret_addr'], '''\
        ret_addr = S->PC;
        S->PC = (smite_UWORD)addr;
        NEXT;
    ''')

    POP = (0x04, ['ITEMS', 'COUNT'], [], '')

    DUP = (0x05, ['x', 'ITEMS', 'COUNT'], ['x', 'ITEMS', 'x'], '')

    SWAP = (0x06, ['x', 'ITEMS', 'y', 'COUNT'], ['y', 'ITEMS', 'x'], '')

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
        r = n < (smite_WORD)smite_WORD_BIT ? x << n : 0;
    ''')

    RSHIFT = (0x0d, ['x', 'n'], ['r'], '''\
        r = n < (smite_WORD)smite_WORD_BIT ? (smite_WORD)((smite_UWORD)x >> n) : 0;
    ''')

    ARSHIFT = (0x0e, ['x', 'n'], ['r'], '''\
        r = ARSHIFT(x, n);
    ''')

    SIGN_EXTEND = (0x0f, ['n1', 'size'], ['n2'], '''\
        n2 = n1 << (WORD_BYTES - (1 << size)) * smite_BYTE_BIT;
        n2 = ARSHIFT(n2, (WORD_BYTES - (1 << size)) * smite_BYTE_BIT);
    ''')

    EQ = (0x10, ['a', 'b'], ['flag'], '''\
        flag = a == b;
    ''')

    LT = (0x11, ['a', 'b'], ['flag'], '''\
        flag = a < b;
    ''')

    ULT = (0x12, ['a', 'b'], ['flag'], '''\
        flag = (smite_UWORD)a < (smite_UWORD)b;
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
          RAISE(SMITE_ERR_DIVISION_BY_ZERO);
        q = a / b;
        r = a % b;
    ''')

    UDIVMOD = (0x17, ['a', 'b'], ['q', 'r'], '''\
        if (b == 0)
          RAISE(SMITE_ERR_DIVISION_BY_ZERO);
        q = (smite_WORD)((smite_UWORD)a / (smite_UWORD)b);
        r = (smite_WORD)((smite_UWORD)a % (smite_UWORD)b);
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
        int ret = load(S, S->PC, smite_SIZE_WORD, &n);
        if (ret != 0)
            RAISE(ret);
        S->PC += WORD_BYTES;
    ''')

    LIT_PC_REL = (0x1b, [], ['n'], '''\
        int ret = load(S, S->PC, smite_SIZE_WORD, &n);
        if (ret != 0)
            RAISE(ret);
        n += S->PC;
        S->PC += WORD_BYTES;
    ''')

    LIT_0 = (0x1c, [], ['zero'], '''\
        zero = 0;
    ''')

    LIT_1 = (0x1d, [], ['one'], '''\
        one = 1;
    ''')

    EXT = (0x1e, None, None, '''\
        smite_ext(S);
    ''')

    HALT = (0x1f, [], [], '''\
        RAISE(SMITE_ERR_HALT);
    ''')
