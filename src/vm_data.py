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
    smite_WORD depth;
    POP(&depth);
    S->SDEPTH -= depth;
    ''',

    Opcodes.PUSH: '''
    smite_WORD depth;
    POP(&depth);
    smite_WORD pickee;
    exception = smite_load_stack(S, depth, &pickee);
    PUSH(pickee);
    ''',

    Opcodes.SWAP: '''
    smite_WORD depth;
    POP(&depth);
    smite_WORD swapee;
    exception = smite_load_stack(S, depth, &swapee);
    smite_WORD top;
    POP(&top);
    PUSH(swapee);
    exception = smite_store_stack(S, depth, top);
    ''',

    Opcodes.RPUSH: '''
    smite_WORD depth;
    POP(&depth);
    smite_WORD pickee;
    exception = smite_load_return_stack(S, depth, &pickee);
    PUSH(pickee);
    ''',

    Opcodes.POP2R: '''
    smite_WORD value;
    POP(&value);
    exception = exception == 0 ? smite_push_return_stack(S, value) : exception;
    ''',

    Opcodes.RPOP: '''
    smite_WORD value;
    exception = smite_pop_return_stack(S, &value);
    PUSH(value);
    ''',

    Opcodes.LT: '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(b < a);
    ''',

    Opcodes.EQ: '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a == b);
    ''',

    Opcodes.ULT: '''
    smite_UWORD a;
    POP((smite_WORD *)&a);
    smite_UWORD b;
    POP((smite_WORD *)&b);
    PUSH(b < a);
    ''',

    Opcodes.ADD: '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(b + a);
    ''',

    Opcodes.MUL: '''
    smite_WORD multiplier;
    POP(&multiplier);
    smite_WORD multiplicand;
    POP(&multiplicand);
    PUSH(multiplier * multiplicand);
    ''',

    Opcodes.UDIVMOD: '''
    smite_UWORD divisor;
    POP((smite_WORD *)&divisor);
    smite_UWORD dividend;
    POP((smite_WORD *)&dividend);
    DIVZERO(divisor);
    PUSH(dividend / divisor);
    PUSH(dividend % divisor);
    ''',

    Opcodes.DIVMOD: '''
    smite_WORD divisor;
    POP(&divisor);
    smite_WORD dividend;
    POP(&dividend);
    DIVZERO(divisor);
    PUSH(dividend / divisor);
    PUSH(dividend % divisor);
    ''',

    Opcodes.NEGATE: '''
    smite_WORD a;
    POP(&a);
    PUSH(-a);
    ''',

    Opcodes.INVERT: '''
    smite_WORD a;
    POP(&a);
    PUSH(~a);
    ''',

    Opcodes.AND: '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a & b);
    ''',

    Opcodes.OR: '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a | b);
    ''',

    Opcodes.XOR: '''
    smite_WORD a;
    POP(&a);
    smite_WORD b;
    POP(&b);
    PUSH(a ^ b);
    ''',

    Opcodes.LSHIFT: '''
    smite_WORD shift;
    POP(&shift);
    smite_WORD value;
    POP(&value);
    PUSH(shift < (smite_WORD)smite_word_bit ? value << shift : 0);
    ''',

    Opcodes.RSHIFT: '''
    smite_WORD shift;
    POP(&shift);
    smite_WORD value;
    POP(&value);
    PUSH(shift < (smite_WORD)smite_word_bit ? (smite_WORD)((smite_UWORD)value >> shift) : 0);
    ''',

    Opcodes.LOAD: '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD value;
    exception = exception ? exception : smite_load_word(S, addr, &value);
    PUSH(value);
    ''',

    Opcodes.STORE: '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD value;
    POP(&value);
    exception = exception ? exception : smite_store_word(S, addr, value);
    ''',

    Opcodes.LOADB: '''
    smite_WORD addr;
    POP(&addr);
    smite_BYTE value;
    exception = exception ? exception : smite_load_byte(S, addr, &value);
    PUSH((smite_WORD)value);
    ''',

    Opcodes.STOREB: '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD value;
    POP(&value);
    exception = exception ? exception : smite_store_byte(S, addr, (smite_BYTE)value);
    ''',

    Opcodes.BRANCH: '''
    POP((smite_WORD *)&(S->PC));
    ''',

    Opcodes.BRANCHZ: '''
    smite_WORD addr;
    POP(&addr);
    smite_WORD cond;
    POP(&cond);
    if (cond == 0)
        S->PC = addr;
    ''',

    Opcodes.CALL: '''
    exception = smite_push_return_stack(S, S->PC);
    POP((smite_WORD *)&(S->PC));
    ''',

    Opcodes.RET: '''
    exception = smite_pop_return_stack(S, (smite_WORD *)&(S->PC));
    ''',

    Opcodes.THROW: '''
    // The POP macro may set exception
    smite_WORD exception_code;
    POP(&exception_code);
    exception = exception_code;
    ''',

    Opcodes.HALT: '''
    smite_WORD ret;
    POP(&ret);
    return ret;
    ''',

    Opcodes.CALL_NATIVE: '''
    void *address;
    POP_NATIVE_TYPE(void *, &address);
    ((void (*)(smite_state *))(address))(S);
    ''',

    Opcodes.EXTRA: '''
    exception = extra(S);
    ''',

    Opcodes.PUSH_WORD_SIZE: '''
    PUSH(smite_word_size);
    ''',

    Opcodes.PUSH_NATIVE_POINTER_SIZE: '''
    PUSH(smite_native_pointer_size);
    ''',

    Opcodes.PUSH_SDEPTH: '''
    smite_WORD value = S->SDEPTH;
    PUSH(value);
    ''',

    Opcodes.STORE_SDEPTH: '''
    smite_WORD value;
    POP(&value);
    S->SDEPTH = value;
    ''',

    Opcodes.PUSH_RDEPTH: '''
    PUSH(S->RDEPTH);
    ''',

    Opcodes.STORE_RDEPTH: '''
    smite_WORD value;
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
    smite_WORD addr;
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
