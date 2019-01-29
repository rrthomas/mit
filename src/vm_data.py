# VM definition
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
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
    ITYPE = Register(ty="smite_WORD", uty="smite_UWORD")
    I = Register(ty="smite_WORD", uty="smite_UWORD")
    MEMORY = Register(read_only=True)
    SDEPTH = Register()
    S0 = Register("smite_WORDP")
    SSIZE = Register(read_only=True)
    RDEPTH = Register()
    R0 = Register("smite_WORDP")
    RSIZE = Register(read_only=True)
    ENDISM = Register(read_only=True)
    HANDLER = Register()
    BADPC = Register()
    INVALID = Register()

@unique
class Types(IntEnum):
    '''Instruction type opcode.'''
    NUMBER = 0x0
    ACTION = 0x1

class Action:
    '''VM action instruction descriptor.'''
    def __init__(self, opcode, code):
        self.opcode = opcode
        self.code = code

@unique
class Actions(Enum):
    '''VM action instructions.'''
    NOP = Action(0x00, '')

    POP = Action(0x01, '''
    smite_WORD depth;
    POP(&depth);
    S->SDEPTH -= depth;
    ''')

    PUSH = Action(0x02, '''
    smite_WORD depth;
    POP(&depth);
    smite_WORD pickee;
    S->exception = smite_load_stack(S, depth, &pickee);
    PUSH(pickee);
    ''')

    SWAP = Action(0x03, '''
    smite_WORD depth;
    POP(&depth);
    smite_WORD swapee;
    S->exception = smite_load_stack(S, depth, &swapee);
    smite_WORD top;
    POP(&top);
    PUSH(swapee);
    S->exception = smite_store_stack(S, depth, top);
    ''')

    RPUSH = Action(0x04, '''
    smite_WORD depth;
    POP(&depth);
    smite_WORD pickee;
    S->exception = smite_load_return_stack(S, depth, &pickee);
    PUSH(pickee);
    ''')

    POP2R = Action(0x05, '''
    smite_WORD value;
    POP(&value);
    S->exception = S->exception == 0 ? smite_push_return_stack(S, value) : S->exception;
    ''')

    RPOP = Action(0x06, '''
    smite_WORD value;
    S->exception = smite_pop_return_stack(S, &value);
    PUSH(value);
    ''')

    LT = Action(0x07, '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(b < a);
    ''')

    EQ = Action(0x08, '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a == b);
    ''')

    ULT = Action(0x09, '''
    smite_UWORD a;
    POP((smite_WORD *)&a);
    smite_UWORD b;
    POP((smite_WORD *)&b);
    PUSH(b < a);
    ''')

    ADD = Action(0x0a, '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(b + a);
    ''')

    NEGATE = Action(0x0b, '''
    smite_WORD a;
    POP(&a);
    PUSH(-a);
    ''')

    MUL = Action(0x0c, '''
    smite_WORD multiplier;
    POP(&multiplier);
    smite_WORD multiplicand;
    POP(&multiplicand);
    PUSH(multiplier * multiplicand);
    ''')

    UDIVMOD = Action(0x0d, '''
    smite_UWORD divisor;
    POP((smite_WORD *)&divisor);
    smite_UWORD dividend;
    POP((smite_WORD *)&dividend);
    DIVZERO(divisor);
    PUSH(dividend / divisor);
    PUSH(dividend % divisor);
    ''')

    DIVMOD = Action(0x0e, '''
    smite_WORD divisor;
    POP(&divisor);
    smite_WORD dividend;
    POP(&dividend);
    DIVZERO(divisor);
    PUSH(dividend / divisor);
    PUSH(dividend % divisor);
    ''')

    INVERT = Action(0x0f, '''
    smite_WORD a;
    POP(&a);
    PUSH(~a);
    ''')

    AND = Action(0x10, '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a & b);
    ''')

    OR = Action(0x11, '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a | b);
    ''')

    XOR = Action(0x12, '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a ^ b);
    ''')

    LSHIFT = Action(0x13, '''
    smite_WORD shift;
    POP(&shift);
    smite_WORD value;
    POP(&value);
    PUSH(shift < (smite_WORD)smite_word_bit ? value << shift : 0);
    ''')

    RSHIFT = Action(0x14, '''
    smite_WORD shift;
    POP(&shift);
    smite_WORD value;
    POP(&value);
    PUSH(shift < (smite_WORD)smite_word_bit ? (smite_WORD)((smite_UWORD)value >> shift) : 0);
    ''')

    LOAD = Action(0x15, '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD value;
    S->exception = S->exception ? S->exception : smite_load_word(S, addr, &value);
    PUSH(value);
    ''')

    STORE = Action(0x16, '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD value;
    POP(&value);
    S->exception = S->exception ? S->exception : smite_store_word(S, addr, value);
    ''')

    LOADB = Action(0x17, '''
    smite_WORD addr;
    POP(&addr);
    smite_BYTE value;
    S->exception = S->exception ? S->exception : smite_load_byte(S, addr, &value);
    PUSH((smite_WORD)value);
    ''')

    STOREB = Action(0x18, '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD value;
    POP(&value);
    S->exception = S->exception ? S->exception : smite_store_byte(S, addr, (smite_BYTE)value);
    ''')

    BRANCH = Action(0x19, '''
    POP((smite_WORD *)&(S->PC));
    ''')

    BRANCHZ = Action(0x1a, '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD cond;
    POP(&cond);
    if (cond == 0)
        S->PC = addr;
    ''')

    CALL = Action(0x1b, '''
    S->exception = smite_push_return_stack(S, S->PC);
    POP((smite_WORD *)&(S->PC));
    ''')

    RET = Action(0x1c, '''
    S->exception = smite_pop_return_stack(S, (smite_WORD *)&(S->PC));
    ''')

    THROW = Action(0x1d, '''
    /* The POP macro may set exception */
    smite_WORD exception_code;
    POP(&exception_code);
    S->exception = exception_code;
    ''')

    HALT = Action(0x1e, '''
    smite_WORD ret;
    POP(&ret);
    S->halt_code = ret;
    RAISE(-255);
    ''')

    CALL_NATIVE = Action(0x1f, '''
    void *address;
    POP_NATIVE_TYPE(void *, &address);
    ((void (*)(smite_state *))(address))(S);
    ''')

    EXTRA = Action(0x20, '''
    smite_WORD ret;
    if ((ret = smite_extra(S)) != 0)
        RAISE(ret);
    ''')

    PUSH_WORD_SIZE = Action(0x21, '''
    PUSH(smite_word_size);
    ''')

    PUSH_NATIVE_POINTER_SIZE = Action(0x22, '''
    PUSH(smite_native_pointer_size);
    ''')

    PUSH_SDEPTH = Action(0x23, '''
    smite_WORD value = S->SDEPTH;
    PUSH(value);
    ''')

    STORE_SDEPTH = Action(0x24, '''
    smite_WORD value;
    POP(&value);
    S->SDEPTH = value;
    ''')

    PUSH_RDEPTH = Action(0x25, '''
    PUSH(S->RDEPTH);
    ''')

    STORE_RDEPTH = Action(0x26, '''
    smite_WORD value;
    POP(&value);
    S->RDEPTH = value;
    ''')

    PUSH_PC = Action(0x27, '''
    PUSH(S->PC);
    ''')

    PUSH_SSIZE = Action(0x28, '''
    PUSH(S->SSIZE);
    ''')

    PUSH_RSIZE = Action(0x29, '''
    PUSH(S->RSIZE);
    ''')

    PUSH_HANDLER = Action(0x2a, '''
    PUSH(S->HANDLER);
    ''')

    STORE_HANDLER = Action(0x2b, '''
    smite_WORD addr;
    POP(&addr);
    S->HANDLER = addr;
    ''')

    PUSH_MEMORY = Action(0x2c, '''
    PUSH(S->MEMORY);
    ''')

    PUSH_BADPC = Action(0x2d, '''
    PUSH(S->BADPC);
    ''')

    PUSH_INVALID = Action(0x2e, '''
    PUSH(S->INVALID);
    ''')
