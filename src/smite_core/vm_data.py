# VM definition
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, IntEnum, unique
from .instruction_gen import Instruction

class Register:
    '''VM register descriptor.'''
    def __init__(self, ty=None, uty=None, read_only=False):
        self.ty = ty or "smite_UWORD"
        self.uty = uty or self.ty
        self.read_only = read_only

@unique
class Registers(Enum):
    '''VM registers.'''
    PC = Register()
    BAD = Register(read_only=True)
    MEMORY = Register(read_only=True)
    STACK_DEPTH = Register()
    S0 = Register("smite_WORDP", read_only=True)
    STACK_SIZE = Register(read_only=True)
    ENDISM = Register(read_only=True)

@unique
class Instructions(Enum):
    '''VM instruction instructions.'''
    HALT = Instruction(0x00, [], [], '''\
        RAISE(SMITE_ERR_HALT);
    ''')

    POP = Instruction(0x01, ['item',], [], '''\
    ''')

    DUP = Instruction(0x02, ['ITEMS', 'COUNT'], ['ITEMS', 'dupee'], '''\
        UNCHECKED_LOAD_STACK(COUNT, &dupee);
    ''')

    SWAP = Instruction(0x03, ['ITEMS', 'COUNT'], ['ITEMS'], '''\
        if (COUNT > 0) {
            smite_WORD top, swapee;
            UNCHECKED_LOAD_STACK(COUNT, &swapee);
            UNCHECKED_LOAD_STACK(0, &top);
            UNCHECKED_STORE_STACK(COUNT, top);
            UNCHECKED_STORE_STACK(0, swapee);
        }
    ''')

    LIT = Instruction(0x04, [], ['n'], '''\
        int ret = LOAD_IMMEDIATE_WORD(S, S->PC, &n);
        if (ret != 0)
            RAISE(ret);
        S->PC += WORD_SIZE;
    ''')

    LIT_PC_REL = Instruction(0x05, [], ['n'], '''\
        int ret = LOAD_IMMEDIATE_WORD(S, S->PC, &n);
        if (ret != 0)
            RAISE(ret);
        n += S->PC;
        S->PC += WORD_SIZE;
    ''')

    NOT = Instruction(0x06, ['x'], ['r'], '''\
        r = ~x;
    ''')

    AND = Instruction(0x07, ['x', 'y'], ['r'], '''\
        r = x & y;
    ''')

    OR = Instruction(0x08, ['x', 'y'], ['r'], '''\
        r = x | y;
    ''')

    XOR = Instruction(0x09, ['x', 'y'], ['r'], '''\
        r = x ^ y;
    ''')

    LSHIFT = Instruction(0x0a, ['x', 'n'], ['r'], '''\
        r = n < (smite_WORD)smite_word_bit ? x << n : 0;
    ''')

    RSHIFT = Instruction(0x0b, ['x', 'n'], ['r'], '''\
        r = n < (smite_WORD)smite_word_bit ? (smite_WORD)((smite_UWORD)x >> n) : 0;
    ''')

    ARSHIFT = Instruction(0x0c, ['x', 'n'], ['r'], '''\
        r = ARSHIFT(x, n);
    ''')

    EQ = Instruction(0x0d, ['a', 'b'], ['flag'], '''\
        flag = a == b;
    ''')

    LT = Instruction(0x0e, ['a', 'b'], ['flag'], '''\
        flag = a < b;
    ''')

    ULT = Instruction(0x0f, ['a', 'b'], ['flag'], '''\
        flag = (smite_UWORD)a < (smite_UWORD)b;
    ''')

    NEGATE = Instruction(0x10, ['a'], ['r'], '''\
        r = -a;
    ''')

    ADD = Instruction(0x11, ['a', 'b'], ['r'], '''\
        r = a + b;
    ''')

    MUL = Instruction(0x12, ['a', 'b'], ['r'], '''\
        r = a * b;
    ''')

    DIVMOD = Instruction(0x13, ['a', 'b'], ['q', 'r'], '''\
        if (b == 0)
          RAISE(SMITE_ERR_DIVISION_BY_ZERO);
        q = a / b;
        r = a % b;
    ''')

    UDIVMOD = Instruction(0x14, ['a', 'b'], ['q', 'r'], '''\
        if (b == 0)
          RAISE(SMITE_ERR_DIVISION_BY_ZERO);
        q = (smite_WORD)((smite_UWORD)a / (smite_UWORD)b);
        r = (smite_WORD)((smite_UWORD)a % (smite_UWORD)b);
    ''')

    LOAD = Instruction(0x15, ['addr'], ['x'], '''\
        int ret = load_word(S, addr, &x);
        if (ret != 0)
            RAISE(ret);
    ''')

    STORE = Instruction(0x16, ['x', 'addr'], [], '''\
        int ret = store_word(S, addr, x);
        if (ret != 0)
            RAISE(ret);
    ''')

    LOADB = Instruction(0x17, ['addr'], ['x'], '''\
        smite_BYTE b_;
        int ret = load_byte(S, addr, &b_);
        if (ret != 0)
            RAISE(ret);
        x = (smite_WORD)b_;
    ''')

    STOREB = Instruction(0x18, ['x', 'addr'], [], '''\
        int ret = store_byte(S, addr, (smite_BYTE)x);
        if (ret != 0)
            RAISE(ret);
    ''')

    BRANCH = Instruction(0x19, ['addr'], [], '''\
        S->PC = (smite_UWORD)addr;
    ''')

    BRANCHZ = Instruction(0x1a, ['flag', 'addr'], [], '''\
        if (flag == 0)
            S->PC = (smite_UWORD)addr;
    ''')

    CALL = Instruction(0x1b, ['addr'], ['ret_addr'], '''\
        ret_addr = S->PC;
        S->PC = (smite_UWORD)addr;
    ''')

    GET_WORD_SIZE = Instruction(0x1c, [], ['r'], '''\
        r = WORD_SIZE;
    ''')

    GET_STACK_DEPTH = Instruction(0x1d, [], ['r'], '''\
        r = S->STACK_DEPTH;
    ''')

    SET_STACK_DEPTH = Instruction(0x1e, ['a'], [], '''\
        if ((smite_UWORD)a > S->STACK_SIZE) {
            S->BAD = a - S->STACK_SIZE;
            RAISE(SMITE_ERR_STACK_OVERFLOW);
        }
        S->STACK_DEPTH = a;
    ''')

    NOP = Instruction(0x1f, [], [], '''\
        // Do nothing.'''
    )
