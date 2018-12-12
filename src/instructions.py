import enum

class Opcodes(enum.IntEnum):
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
    PUSH_PSIZE = 0x21
    PUSH_SP = 0x22
    STORE_SP = 0x23
    PUSH_RP = 0x24
    STORE_RP = 0x25
    PUSH_PC = 0x26
    PUSH_S0 = 0x27
    PUSH_SSIZE = 0x28
    PUSH_R0 = 0x29
    PUSH_RSIZE = 0x2a
    PUSH_HANDLER = 0x2b
    STORE_HANDLER = 0x2c
    PUSH_MEMORY = 0x2d
    PUSH_BADPC = 0x2e
    PUSH_INVALID = 0x2f

actions = {}

actions[Opcodes.NOP] = '''
'''

actions[Opcodes.POP] = '''
WORD depth = POP;
SP -= depth * WORD_W * STACK_DIRECTION;
'''

actions[Opcodes.PUSH] = '''
WORD depth = POP;
WORD pickee = LOAD_WORD(SP - depth * WORD_W * STACK_DIRECTION);
PUSH(pickee);
'''

actions[Opcodes.SWAP] = '''
WORD depth = POP;
WORD swapee = LOAD_WORD(SP - depth * WORD_W * STACK_DIRECTION);
WORD top = POP;
PUSH(swapee);
STORE_WORD(SP - depth * WORD_W * STACK_DIRECTION, top);
'''

actions[Opcodes.RPUSH] = '''
WORD depth = POP;
WORD pickee = LOAD_WORD(RP - depth * WORD_W * STACK_DIRECTION);
PUSH(pickee);
'''

actions[Opcodes.POP2R] = '''
WORD value = POP;
PUSH_RETURN(value);
'''

actions[Opcodes.RPOP] = '''
WORD value = POP_RETURN;
PUSH(value);
'''

actions[Opcodes.LT] = '''
WORD a = POP;
WORD b = POP;
PUSH(b < a);
'''

actions[Opcodes.EQ] = '''
WORD a = POP;
WORD b = POP;
PUSH(a == b);
'''

actions[Opcodes.ULT] = '''
UWORD a = POP;
UWORD b = POP;
PUSH(b < a);
'''

actions[Opcodes.ADD] = '''
WORD a = POP;
WORD b = POP;
PUSH(b + a);
'''

actions[Opcodes.MUL] = '''
WORD multiplier = POP;
WORD multiplicand = POP;
PUSH(multiplier * multiplicand);
'''

actions[Opcodes.UDIVMOD] = '''
UWORD divisor = POP;
UWORD dividend = POP;
DIVZERO(divisor);
PUSH(dividend / divisor);
PUSH(dividend % divisor);
'''

actions[Opcodes.DIVMOD] = '''
WORD divisor = POP;
WORD dividend = POP;
DIVZERO(divisor);
PUSH(dividend / divisor);
PUSH(dividend % divisor);
'''

actions[Opcodes.NEGATE] = '''
WORD a = POP;
PUSH(-a);
'''

actions[Opcodes.INVERT] = '''
WORD a = POP;
PUSH(~a);
'''

actions[Opcodes.AND] = '''
WORD a = POP;
WORD b = POP;
PUSH(a & b);
'''

actions[Opcodes.OR] = '''
WORD a = POP;
WORD b = POP;
PUSH(a | b);
'''

actions[Opcodes.XOR] = '''
WORD a = POP;
WORD b = POP;
PUSH(a ^ b);
'''

actions[Opcodes.LSHIFT] = '''
WORD shift = POP;
WORD value = POP;
PUSH(shift < (WORD)WORD_BIT ? value << shift : 0);
'''

actions[Opcodes.RSHIFT] = '''
WORD shift = POP;
WORD value = POP;
PUSH(shift < (WORD)WORD_BIT ? (WORD)((UWORD)value >> shift) : 0);
'''

actions[Opcodes.LOAD] = '''
WORD addr = POP;
WORD value = LOAD_WORD(addr);
PUSH(value);
'''

actions[Opcodes.STORE] = '''
WORD addr = POP;
WORD value = POP;
STORE_WORD(addr, value);
'''

actions[Opcodes.LOADB] = '''
WORD addr = POP;
BYTE value = LOAD_BYTE(addr);
PUSH((WORD)value);
'''

actions[Opcodes.STOREB] = '''
WORD addr = POP;
BYTE value = (BYTE)POP;
STORE_BYTE(addr, value);
'''

actions[Opcodes.BRANCH] = '''
PC = POP;
'''

actions[Opcodes.BRANCHZ] = '''
WORD addr = POP;
if (POP == 0)
    PC = addr;
'''

actions[Opcodes.CALL] = '''
PUSH_RETURN(PC);
PC = POP;
'''

actions[Opcodes.RET] = '''
PC = POP_RETURN;
'''

actions[Opcodes.THROW] = '''
exception = POP;
'''

actions[Opcodes.HALT] = '''
return POP;
'''

actions[Opcodes.CALL_NATIVE] = '''
WORD_pointer address;
for (int i = POINTER_W - 1; i >= 0; i--)
    address.words[i] = POP;
address.pointer();
'''

actions[Opcodes.EXTRA] = '''
extra();
'''

actions[Opcodes.PUSH_PSIZE] = '''
PUSH(POINTER_W);
'''

actions[Opcodes.PUSH_SP] = '''
WORD value = SP;
PUSH(value);
'''

actions[Opcodes.STORE_SP] = '''
WORD value = POP;
CHECK_ALIGNED(value);
if (exception == 0)
    SP = value;
'''

actions[Opcodes.PUSH_RP] = '''
PUSH(RP);
'''

actions[Opcodes.STORE_RP] = '''
WORD value = POP;
CHECK_ALIGNED(value);
if (exception == 0)
    RP = value;
'''

actions[Opcodes.PUSH_PC] = '''
PUSH(PC);
'''

actions[Opcodes.PUSH_S0] = '''
PUSH(S0);
'''

actions[Opcodes.PUSH_SSIZE] = '''
PUSH(HASHS);
'''

actions[Opcodes.PUSH_R0] = '''
PUSH(R0);
'''

actions[Opcodes.PUSH_RSIZE] = '''
PUSH(HASHR);
'''

actions[Opcodes.PUSH_HANDLER] = '''
PUSH(HANDLER);
'''

actions[Opcodes.STORE_HANDLER] = '''
HANDLER = POP;
'''

actions[Opcodes.PUSH_MEMORY] = '''
PUSH(MEMORY);
'''

actions[Opcodes.PUSH_BADPC] = '''
PUSH(BADPC);
'''

actions[Opcodes.PUSH_INVALID] = '''
PUSH(INVALID);
'''
