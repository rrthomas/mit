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
        self.ty = ty or "UWORD"
        self.uty = uty or self.ty
        self.read_only = read_only

@unique
class Registers(Enum):
    PC = Register()
    ITYPE = Register(ty="WORD", uty="UWORD")
    I = Register(ty="WORD", uty="UWORD")
    MEMORY = Register(read_only=True)
    SDEPTH = Register()
    S0 = Register("WORDP")
    SSIZE = Register(read_only=True)
    RDEPTH = Register()
    R0 = Register("WORDP")
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

# FIXME: Make a single Actions enumeration
@unique
class Opcodes(IntEnum):
    '''Action opcode.'''
    NOP = 0x00
    POP = 0x01
    PUSH = 0x02
    SWAP = 0x03
    RPUSH = 0x04
    POP2R = 0x05
    RPOP = 0x06
    LT = 0x07
    EQ = 0x08
    ULT = 0x09
    ADD = 0x0a
    MUL = 0x0b
    UDIVMOD = 0x0c
    DIVMOD = 0x0d
    NEGATE = 0x0e
    INVERT = 0x0f
    AND = 0x10
    OR = 0x11
    XOR = 0x12
    LSHIFT = 0x13
    RSHIFT = 0x14
    LOAD = 0x15
    STORE = 0x16
    LOADB = 0x17
    STOREB = 0x18
    BRANCH = 0x19
    BRANCHZ = 0x1a
    CALL = 0x1b
    RET = 0x1c
    THROW = 0x1d
    HALT = 0x1e
    CALL_NATIVE = 0x1f
    EXTRA = 0x20
    PUSH_WORD_SIZE = 0x21
    PUSH_NATIVE_POINTER_SIZE = 0x22
    PUSH_SDEPTH = 0x23
    STORE_SDEPTH = 0x24
    PUSH_RDEPTH = 0x25
    STORE_RDEPTH = 0x26
    PUSH_PC = 0x27
    PUSH_SSIZE = 0x28
    PUSH_RSIZE = 0x29
    PUSH_HANDLER = 0x2a
    STORE_HANDLER = 0x2b
    PUSH_MEMORY = 0x2c
    PUSH_BADPC = 0x2d
    PUSH_INVALID = 0x2e

Actions = {
    Opcodes.NOP: '''''',

    Opcodes.POP: '''
    WORD depth;
    POP(&depth);
    S->SDEPTH -= depth;
    ''',

    Opcodes.PUSH: '''
    WORD depth;
    POP(&depth);
    WORD pickee;
    exception = load_stack(S, depth, &pickee);
    PUSH(pickee);
    ''',

    Opcodes.SWAP: '''
    WORD depth;
    POP(&depth);
    WORD swapee;
    exception = load_stack(S, depth, &swapee);
    WORD top;
    POP(&top);
    PUSH(swapee);
    exception = store_stack(S, depth, top);
    ''',

    Opcodes.RPUSH: '''
    WORD depth;
    POP(&depth);
    WORD pickee;
    exception = load_return_stack(S, depth, &pickee);
    PUSH(pickee);
    ''',

    Opcodes.POP2R: '''
    WORD value;
    POP(&value);
    exception = exception == 0 ? push_return_stack(S, value) : exception;
    ''',

    Opcodes.RPOP: '''
    WORD value;
    exception = pop_return_stack(S, &value);
    PUSH(value);
    ''',

    Opcodes.LT: '''
    WORD a;
    POP(&a);
    WORD b;
    POP(&b);
    PUSH(b < a);
    ''',

    Opcodes.EQ: '''
    WORD a;
    POP(&a);
    WORD b;
    POP(&b);
    PUSH(a == b);
    ''',

    Opcodes.ULT: '''
    UWORD a;
    POP((WORD *)&a);
    UWORD b;
    POP((WORD *)&b);
    PUSH(b < a);
    ''',

    Opcodes.ADD: '''
    WORD a;
    POP(&a);
    WORD b;
    POP(&b);
    PUSH(b + a);
    ''',

    Opcodes.MUL: '''
    WORD multiplier;
    POP(&multiplier);
    WORD multiplicand;
    POP(&multiplicand);
    PUSH(multiplier * multiplicand);
    ''',

    Opcodes.UDIVMOD: '''
    UWORD divisor;
    POP((WORD *)&divisor);
    UWORD dividend;
    POP((WORD *)&dividend);
    DIVZERO(divisor);
    PUSH(dividend / divisor);
    PUSH(dividend % divisor);
    ''',

    Opcodes.DIVMOD: '''
    WORD divisor;
    POP(&divisor);
    WORD dividend;
    POP(&dividend);
    DIVZERO(divisor);
    PUSH(dividend / divisor);
    PUSH(dividend % divisor);
    ''',

    Opcodes.NEGATE: '''
    WORD a;
    POP(&a);
    PUSH(-a);
    ''',

    Opcodes.INVERT: '''
    WORD a;
    POP(&a);
    PUSH(~a);
    ''',

    Opcodes.AND: '''
    WORD a;
    POP(&a);
    WORD b;
    POP(&b);
    PUSH(a & b);
    ''',

    Opcodes.OR: '''
    WORD a;
    POP(&a);
    WORD b;
    POP(&b);
    PUSH(a | b);
    ''',

    Opcodes.XOR: '''
    WORD a;
    POP(&a);
    WORD b;
    POP(&b);
    PUSH(a ^ b);
    ''',

    Opcodes.LSHIFT: '''
    WORD shift;
    POP(&shift);
    WORD value;
    POP(&value);
    PUSH(shift < (WORD)word_bit ? value << shift : 0);
    ''',

    Opcodes.RSHIFT: '''
    WORD shift;
    POP(&shift);
    WORD value;
    POP(&value);
    PUSH(shift < (WORD)word_bit ? (WORD)((UWORD)value >> shift) : 0);
    ''',

    Opcodes.LOAD: '''
    WORD addr;
    POP(&addr);
    WORD value;
    exception = exception ? exception : load_word(S, addr, &value);
    PUSH(value);
    ''',

    Opcodes.STORE: '''
    WORD addr;
    POP(&addr);
    WORD value;
    POP(&value);
    exception = exception ? exception : store_word(S, addr, value);
    ''',

    Opcodes.LOADB: '''
    WORD addr;
    POP(&addr);
    BYTE value;
    exception = exception ? exception : load_byte(S, addr, &value);
    PUSH((WORD)value);
    ''',

    Opcodes.STOREB: '''
    WORD addr;
    POP(&addr);
    WORD value;
    POP(&value);
    exception = exception ? exception : store_byte(S, addr, (BYTE)value);
    ''',

    Opcodes.BRANCH: '''
    POP((WORD *)&(S->PC));
    ''',

    Opcodes.BRANCHZ: '''
    WORD addr;
    POP(&addr);
    WORD cond;
    POP(&cond);
    if (cond == 0)
        S->PC = addr;
    ''',

    Opcodes.CALL: '''
    exception = push_return_stack(S, S->PC);
    POP((WORD *)&(S->PC));
    ''',

    Opcodes.RET: '''
    exception = pop_return_stack(S, (WORD *)&(S->PC));
    ''',

    Opcodes.THROW: '''
    // The POP macro may set exception
    WORD exception_code;
    POP(&exception_code);
    exception = exception_code;
    ''',

    Opcodes.HALT: '''
    WORD ret;
    POP(&ret);
    return ret;
    ''',

    Opcodes.CALL_NATIVE: '''
    void *address;
    POP_NATIVE_TYPE(void *, &address);
    ((void (*)(state *))(address))(S);
    ''',

    Opcodes.EXTRA: '''
    exception = extra(S);
    ''',

    Opcodes.PUSH_WORD_SIZE: '''
    PUSH(word_size);
    ''',

    Opcodes.PUSH_NATIVE_POINTER_SIZE: '''
    PUSH(native_pointer_size);
    ''',

    Opcodes.PUSH_SDEPTH: '''
    WORD value = S->SDEPTH;
    PUSH(value);
    ''',

    Opcodes.STORE_SDEPTH: '''
    WORD value;
    POP(&value);
    S->SDEPTH = value;
    ''',

    Opcodes.PUSH_RDEPTH: '''
    PUSH(S->RDEPTH);
    ''',

    Opcodes.STORE_RDEPTH: '''
    WORD value;
    POP(&value);
    S->RDEPTH = value;
    ''',

    Opcodes.PUSH_PC: '''
    PUSH(S->PC);
    ''',

    Opcodes.PUSH_SSIZE: '''
    PUSH(S->SSIZE);
    ''',

    Opcodes.PUSH_RSIZE: '''
    PUSH(S->RSIZE);
    ''',

    Opcodes.PUSH_HANDLER: '''
    PUSH(S->HANDLER);
    ''',

    Opcodes.STORE_HANDLER: '''
    WORD addr;
    POP(&addr);
    S->HANDLER = addr;
    ''',

    Opcodes.PUSH_MEMORY: '''
    PUSH(S->MEMORY);
    ''',

    Opcodes.PUSH_BADPC: '''
    PUSH(S->BADPC);
    ''',

    Opcodes.PUSH_INVALID: '''
    PUSH(S->INVALID);
    ''',
}
