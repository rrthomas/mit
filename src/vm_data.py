# VM definition
#
# (c) Reuben Thomas 1994-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from enum import IntEnum

class Register:
    '''VM register descriptor.'''
    def __init__(self, name, ty=None, uty=None, read_only=False):
        self.name = name
        self.ty = ty or "UWORD"
        self.uty = uty or self.ty
        self.read_only = read_only

registers = [
    Register("PC"),
    Register("ITYPE", ty="WORD", uty="UWORD"),
    Register("I", ty="WORD", uty="UWORD"),
    Register("MEMORY", read_only=True),
    Register("SDEPTH"),
    Register("S0", "WORDP"),
    Register("SSIZE", read_only=True),
    Register("RDEPTH"),
    Register("R0", "WORDP"),
    Register("RSIZE", read_only=True),
    Register("ENDISM", read_only=True),
    Register("HANDLER"),
    Register("BADPC"),
    Register("INVALID"),
]

class Types(IntEnum):
    '''Instruction type opcode.'''
    NUMBER = 0x0
    ACTION = 0x1

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

actions = {}

actions[Opcodes.NOP] = '''
'''

actions[Opcodes.POP] = '''
WORD depth;
POP(&depth);
S->SDEPTH -= depth;
'''

actions[Opcodes.PUSH] = '''
WORD depth;
POP(&depth);
WORD pickee;
exception = load_stack(S, depth, &pickee);
PUSH(pickee);
'''

actions[Opcodes.SWAP] = '''
WORD depth;
POP(&depth);
WORD swapee;
exception = load_stack(S, depth, &swapee);
WORD top;
POP(&top);
PUSH(swapee);
exception = store_stack(S, depth, top);
'''

actions[Opcodes.RPUSH] = '''
WORD depth;
POP(&depth);
WORD pickee;
exception = load_return_stack(S, depth, &pickee);
PUSH(pickee);
'''

actions[Opcodes.POP2R] = '''
WORD value;
POP(&value);
exception = exception == 0 ? push_return_stack(S, value) : exception;
'''

actions[Opcodes.RPOP] = '''
WORD value;
exception = pop_return_stack(S, &value);
PUSH(value);
'''

actions[Opcodes.LT] = '''
WORD a;
POP(&a);
WORD b;
POP(&b);
PUSH(b < a);
'''

actions[Opcodes.EQ] = '''
WORD a;
POP(&a);
WORD b;
POP(&b);
PUSH(a == b);
'''

actions[Opcodes.ULT] = '''
UWORD a;
POP((WORD *)&a);
UWORD b;
POP((WORD *)&b);
PUSH(b < a);
'''

actions[Opcodes.ADD] = '''
WORD a;
POP(&a);
WORD b;
POP(&b);
PUSH(b + a);
'''

actions[Opcodes.MUL] = '''
WORD multiplier;
POP(&multiplier);
WORD multiplicand;
POP(&multiplicand);
PUSH(multiplier * multiplicand);
'''

actions[Opcodes.UDIVMOD] = '''
UWORD divisor;
POP((WORD *)&divisor);
UWORD dividend;
POP((WORD *)&dividend);
DIVZERO(divisor);
PUSH(dividend / divisor);
PUSH(dividend % divisor);
'''

actions[Opcodes.DIVMOD] = '''
WORD divisor;
POP(&divisor);
WORD dividend;
POP(&dividend);
DIVZERO(divisor);
PUSH(dividend / divisor);
PUSH(dividend % divisor);
'''

actions[Opcodes.NEGATE] = '''
WORD a;
POP(&a);
PUSH(-a);
'''

actions[Opcodes.INVERT] = '''
WORD a;
POP(&a);
PUSH(~a);
'''

actions[Opcodes.AND] = '''
WORD a;
POP(&a);
WORD b;
POP(&b);
PUSH(a & b);
'''

actions[Opcodes.OR] = '''
WORD a;
POP(&a);
WORD b;
POP(&b);
PUSH(a | b);
'''

actions[Opcodes.XOR] = '''
WORD a;
POP(&a);
WORD b;
POP(&b);
PUSH(a ^ b);
'''

actions[Opcodes.LSHIFT] = '''
WORD shift;
POP(&shift);
WORD value;
POP(&value);
PUSH(shift < (WORD)word_bit ? value << shift : 0);
'''

actions[Opcodes.RSHIFT] = '''
WORD shift;
POP(&shift);
WORD value;
POP(&value);
PUSH(shift < (WORD)word_bit ? (WORD)((UWORD)value >> shift) : 0);
'''

actions[Opcodes.LOAD] = '''
WORD addr;
POP(&addr);
WORD value;
exception = exception ? exception : load_word(S, addr, &value);
PUSH(value);
'''

actions[Opcodes.STORE] = '''
WORD addr;
POP(&addr);
WORD value;
POP(&value);
exception = exception ? exception : store_word(S, addr, value);
'''

actions[Opcodes.LOADB] = '''
WORD addr;
POP(&addr);
BYTE value;
exception = exception ? exception : load_byte(S, addr, &value);
PUSH((WORD)value);
'''

actions[Opcodes.STOREB] = '''
WORD addr;
POP(&addr);
WORD value;
POP(&value);
exception = exception ? exception : store_byte(S, addr, (BYTE)value);
'''

actions[Opcodes.BRANCH] = '''
POP((WORD *)&(S->PC));
'''

actions[Opcodes.BRANCHZ] = '''
WORD addr;
POP(&addr);
WORD cond;
POP(&cond);
if (cond == 0)
    S->PC = addr;
'''

actions[Opcodes.CALL] = '''
exception = push_return_stack(S, S->PC);
POP((WORD *)&(S->PC));
'''

actions[Opcodes.RET] = '''
exception = pop_return_stack(S, (WORD *)&(S->PC));
'''

actions[Opcodes.THROW] = '''
// The POP macro may set exception
WORD exception_code;
POP(&exception_code);
exception = exception_code;
'''

actions[Opcodes.HALT] = '''
WORD ret;
POP(&ret);
return ret;
'''

actions[Opcodes.CALL_NATIVE] = '''
void *address;
POP_NATIVE_TYPE(void *, &address);
((void (*)(state *))(address))(S);
'''

actions[Opcodes.EXTRA] = '''
exception = extra(S);
'''

actions[Opcodes.PUSH_WORD_SIZE] = '''
PUSH(word_size);
'''

actions[Opcodes.PUSH_NATIVE_POINTER_SIZE] = '''
PUSH(native_pointer_size);
'''

actions[Opcodes.PUSH_SDEPTH] = '''
WORD value = S->SDEPTH;
PUSH(value);
'''

actions[Opcodes.STORE_SDEPTH] = '''
WORD value;
POP(&value);
S->SDEPTH = value;
'''

actions[Opcodes.PUSH_RDEPTH] = '''
PUSH(S->RDEPTH);
'''

actions[Opcodes.STORE_RDEPTH] = '''
WORD value;
POP(&value);
S->RDEPTH = value;
'''

actions[Opcodes.PUSH_PC] = '''
PUSH(S->PC);
'''

actions[Opcodes.PUSH_SSIZE] = '''
PUSH(S->SSIZE);
'''

actions[Opcodes.PUSH_RSIZE] = '''
PUSH(S->RSIZE);
'''

actions[Opcodes.PUSH_HANDLER] = '''
PUSH(S->HANDLER);
'''

actions[Opcodes.STORE_HANDLER] = '''
WORD addr;
POP(&addr);
S->HANDLER = addr;
'''

actions[Opcodes.PUSH_MEMORY] = '''
PUSH(S->MEMORY);
'''

actions[Opcodes.PUSH_BADPC] = '''
PUSH(S->BADPC);
'''

actions[Opcodes.PUSH_INVALID] = '''
PUSH(S->INVALID);
'''
