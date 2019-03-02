# VM definition
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, IntEnum, unique

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
    BAD_ADDRESS = Register(read_only=True)
    MEMORY = Register(read_only=True)
    STACK_DEPTH = Register()
    S0 = Register("smite_WORDP", read_only=True)
    STACK_SIZE = Register(read_only=True)
    ENDISM = Register(read_only=True)

@unique
class Types(IntEnum):
    '''Instruction type opcode.'''
    NUMBER = 0x0
    ACTION = 0x1

class Action:
    '''VM action instruction descriptor.

     - opcode - int - SMite opcode number.
     - args - list - list of stack arguments.
     - results - list - list of stack results.
     - code - str - C source code.

    C variables are created for the arguments and results; the arguments are
    pushed and results popped.

    The code should RAISE any error before writing any state, so that if an
    error is raised, the state of the VM is not changed.
    '''
    def __init__(self, opcode, args, results, code):
        self.opcode = opcode
        self.args = args
        self.results = results
        self.code = code

@unique
class Actions(Enum):
    '''VM action instructions.'''
    HALT = Action(0x00, [], [], '''\
        RAISE(0);
    ''')

    POP = Action(0x01, ['depth'], [], '''\
        S->STACK_DEPTH -= depth;
    ''')

    DUP = Action(0x02, ['depth'], ['dupee'], '''\
        RAISE_NON_ZERO(smite_load_stack(S, depth, &dupee));
    ''')

    SWAP = Action(0x03, ['depth'], [], '''\
        if (depth > 0) {
            smite_WORD top, swapee;
            RAISE_NON_ZERO(smite_load_stack(S, depth, &swapee));
            RAISE_NON_ZERO(smite_load_stack(S, 0, &top));
            RAISE_NON_ZERO(smite_store_stack(S, depth, top));
            RAISE_NON_ZERO(smite_store_stack(S, 0, swapee));
        }
    ''')

    ROTATE_UP = Action(0x04, ['depth'], [], '''\
        if (depth >= (smite_WORD)S->STACK_DEPTH) {
            S->BAD_ADDRESS = depth;
            RAISE(3);
        }

        smite_UWORD offset = S->STACK_DEPTH - depth - 1;
        smite_WORD temp = *(S->S0 + offset * STACK_DIRECTION);
        memmove(S->S0 + offset * STACK_DIRECTION,
                S->S0 + (offset + 1) * STACK_DIRECTION,
                (S->STACK_DEPTH - offset) * sizeof(smite_WORD));
        *(S->S0 + (S->STACK_DEPTH - 1) * STACK_DIRECTION) = temp;
    ''')

    ROTATE_DOWN = Action(0x05, ['depth'], [], '''\
        if (depth >= (smite_WORD)S->STACK_DEPTH) {
            S->BAD_ADDRESS = depth;
            RAISE(3);
        }

        smite_UWORD offset = S->STACK_DEPTH - depth - 1;
        smite_WORD temp = *(S->S0 + (S->STACK_DEPTH - 1) * STACK_DIRECTION);
        memmove(S->S0 + (offset + 1) * STACK_DIRECTION,
                S->S0 + offset * STACK_DIRECTION,
                (S->STACK_DEPTH - offset) * sizeof(smite_WORD));
        *(S->S0 + offset * STACK_DIRECTION) = temp;
    ''')

    NOT = Action(0x06, ['x'], ['r'], '''\
        r = ~x;
    ''')

    AND = Action(0x07, ['x', 'y'], ['r'], '''\
        r = x & y;
    ''')

    OR = Action(0x08, ['x', 'y'], ['r'], '''\
        r = x | y;
    ''')

    XOR = Action(0x09, ['x', 'y'], ['r'], '''\
        r = x ^ y;
    ''')

    LSHIFT = Action(0x0a, ['x', 'n'], ['r'], '''\
        r = n < (smite_WORD)smite_word_bit ? x << n : 0;
    ''')

    RSHIFT = Action(0x0b, ['x', 'n'], ['r'], '''\
        r = n < (smite_WORD)smite_word_bit ? (smite_WORD)((smite_UWORD)x >> n) : 0;
    ''')

    ARSHIFT = Action(0x0c, ['x', 'n'], ['r'], '''\
        r = ARSHIFT(x, n);
    ''')

    EQ = Action(0x0d, ['a', 'b'], ['flag'], '''\
        flag = a == b;
    ''')

    LT = Action(0x0e, ['a', 'b'], ['flag'], '''\
        flag = a < b;
    ''')

    ULT = Action(0x0f, ['a', 'b'], ['flag'], '''\
        flag = (smite_UWORD)a < (smite_UWORD)b;
    ''')

    NEGATE = Action(0x10, ['a'], ['r'], '''\
        r = -a;
    ''')

    ADD = Action(0x11, ['a', 'b'], ['r'], '''\
        r = a + b;
    ''')

    MUL = Action(0x12, ['a', 'b'], ['r'], '''\
        r = a * b;
    ''')

    DIVMOD = Action(0x13, ['a', 'b'], ['q', 'r'], '''\
        DIVZERO(b);
        q = a / b;
        r = a % b;
    ''')

    UDIVMOD = Action(0x14, ['a', 'b'], ['q', 'r'], '''\
        DIVZERO(b);
        q = (smite_WORD)((smite_UWORD)a / (smite_UWORD)b);
        r = (smite_WORD)((smite_UWORD)a % (smite_UWORD)b);
    ''')

    LOAD = Action(0x15, ['addr'], ['x'], '''\
        RAISE_NON_ZERO(smite_load_word(S, addr, &x));
    ''')

    STORE = Action(0x16, ['x', 'addr'], [], '''\
        RAISE_NON_ZERO(smite_store_word(S, addr, x));
    ''')

    LOADB = Action(0x17, ['addr'], ['x'], '''\
        smite_BYTE b_;
        RAISE_NON_ZERO(smite_load_byte(S, addr, &b_));
        x = (smite_WORD)b_;
    ''')

    STOREB = Action(0x18, ['x', 'addr'], [], '''\
        RAISE_NON_ZERO(smite_store_byte(S, addr, (smite_BYTE)x));
    ''')

    BRANCH = Action(0x19, ['addr'], [], '''\
        S->PC = (smite_UWORD)addr;
    ''')

    BRANCHZ = Action(0x1a, ['flag', 'addr'], [], '''\
        if (flag == 0)
            S->PC = (smite_UWORD)addr;
    ''')

    CALL = Action(0x1b, ['addr'], ['ret_addr'], '''\
        ret_addr = S->PC;
        S->PC = (smite_UWORD)addr;
    ''')

    GET_WORD_SIZE = Action(0x1c, [], ['r'], '''\
        r = smite_word_size;
    ''')

    GET_STACK_DEPTH = Action(0x1d, [], ['r'], '''\
        r = S->STACK_DEPTH;
    ''')

    SET_STACK_DEPTH = Action(0x1e, ['a'], [], '''\
        if ((smite_UWORD)a > S->STACK_SIZE) {
            S->BAD_ADDRESS = a;
            RAISE(2);
        }
        S->STACK_DEPTH = a;
    ''')

    NOP = Action(0x1f, [], [], '''\
        // Do nothing.'''
    )
