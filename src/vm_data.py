# VM definition
#
# (c) Reuben Thomas 1994-2019
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
    S0 = Register("smite_WORDP")
    F0 = Register()
    FRAME_DEPTH = Register()
    ENDISM = Register(read_only=True)

@unique
class Types(IntEnum):
    '''Instruction type opcode.'''
    NUMBER = 0x0
    ACTION = 0x1

class Action:
    '''
    VM action instruction descriptor.

     - opcode - int - SMite opcode number.
     - code - str - C source code.
    '''
    def __init__(self, opcode, code):
        self.opcode = opcode
        self.code = code

@unique
class Actions(Enum):
    '''VM action instructions.'''
    NOP = Action(0x00, '''\
        // I'm in ur code doing ur nothing.'''
    )

    POP = Action(0x01, '''\
        smite_WORD depth;
        POP(&depth);
        S->FRAME_DEPTH -= depth;
    ''')

    DUP = Action(0x02, '''\
        smite_WORD depth;
        POP(&depth);
        smite_WORD dupee;
        RAISE(smite_load_frame(S, depth, &dupee));
        PUSH(dupee);
    ''')

    SWAP = Action(0x03, '''\
        smite_WORD depth;
        POP(&depth);
        smite_WORD swapee;
        RAISE(smite_load_frame(S, depth, &swapee));
        smite_WORD top;
        POP(&top);
        PUSH(swapee);
        RAISE(smite_store_frame(S, depth, top));
    ''')

    LT = Action(0x04, '''\
        smite_WORD a;
        POP(&a);
        smite_WORD b;
        POP(&b);
        PUSH(b < a);
    ''')

    EQ = Action(0x05, '''\
        smite_WORD a;
        POP(&a);
        smite_WORD b;
        POP(&b);
        PUSH(a == b);
    ''')

    ULT = Action(0x06, '''\
        smite_UWORD a;
        POP((smite_WORD *)&a);
        smite_UWORD b;
        POP((smite_WORD *)&b);
        PUSH(b < a);
    ''')

    ADD = Action(0x07, '''\
        smite_WORD a;
        POP(&a);
        smite_WORD b;
        POP(&b);
        PUSH(b + a);
    ''')

    NEGATE = Action(0x08, '''\
        smite_WORD a;
        POP(&a);
        PUSH(-a);
    ''')

    MUL = Action(0x09, '''\
        smite_WORD multiplier;
        POP(&multiplier);
        smite_WORD multiplicand;
        POP(&multiplicand);
        PUSH(multiplier * multiplicand);
    ''')

    UDIVMOD = Action(0x0a, '''\
        smite_UWORD divisor;
        POP((smite_WORD *)&divisor);
        smite_UWORD dividend;
        POP((smite_WORD *)&dividend);
        DIVZERO(divisor);
        PUSH(dividend / divisor);
        PUSH(dividend % divisor);
    ''')

    DIVMOD = Action(0x0b, '''\
        smite_WORD divisor;
        POP(&divisor);
        smite_WORD dividend;
        POP(&dividend);
        DIVZERO(divisor);
        PUSH(dividend / divisor);
        PUSH(dividend % divisor);
    ''')

    INVERT = Action(0x0c, '''\
        smite_WORD a;
        POP(&a);
        PUSH(~a);
    ''')

    AND = Action(0x0d, '''\
        smite_WORD a;
        POP(&a);
        smite_WORD b;
        POP(&b);
        PUSH(a & b);
    ''')

    OR = Action(0x0e, '''\
        smite_WORD a;
        POP(&a);
        smite_WORD b;
        POP(&b);
        PUSH(a | b);
    ''')

    XOR = Action(0x0f, '''\
        smite_WORD a;
        POP(&a);
        smite_WORD b;
        POP(&b);
        PUSH(a ^ b);
    ''')

    LSHIFT = Action(0x10, '''\
        smite_WORD shift;
        POP(&shift);
        smite_WORD value;
        POP(&value);
        PUSH(shift < (smite_WORD)smite_word_bit ? value << shift : 0);
    ''')

    RSHIFT = Action(0x11, '''\
        smite_WORD shift;
        POP(&shift);
        smite_WORD value;
        POP(&value);
        PUSH(shift < (smite_WORD)smite_word_bit ? (smite_WORD)((smite_UWORD)value >> shift) : 0);
    ''')

    LOAD = Action(0x12, '''\
        smite_WORD addr;
        POP(&addr);
        smite_WORD value;
        RAISE(smite_load_word(S, addr, &value));
        PUSH(value);
    ''')

    STORE = Action(0x13, '''\
        smite_WORD addr;
        POP(&addr);
        smite_WORD value;
        POP(&value);
        RAISE(smite_store_word(S, addr, value));
    ''')

    LOADB = Action(0x14, '''\
        smite_WORD addr;
        POP(&addr);
        smite_BYTE value;
        RAISE(smite_load_byte(S, addr, &value));
        PUSH((smite_WORD)value);
    ''')

    STOREB = Action(0x15, '''\
        smite_WORD addr;
        POP(&addr);
        smite_WORD value;
        POP(&value);
        RAISE(smite_store_byte(S, addr, (smite_BYTE)value));
    ''')

    BRANCH = Action(0x16, '''\
        POP((smite_WORD *)&(S->PC));
    ''')

    BRANCHZ = Action(0x17, '''\
        smite_WORD addr;
        POP(&addr);
        smite_WORD cond;
        POP(&cond);
        if (cond == 0)
            S->PC = addr;
    ''')

    CALL = Action(0x18, '''\
        smite_WORD addr;
        POP(&addr);
        PUSH(S->PC);
        S->PC = addr;
    ''')

    HALT = Action(0x19, '''\
        smite_WORD ret;
        POP(&ret);
        S->halt_code = ret;
        RAISE(-255);
    ''')

    CALL_NATIVE = Action(0x1a, '''\
        void *address;
        POP_NATIVE_TYPE(void *, &address);
        ((void (*)(smite_state *))(address))(S);
    ''')

    EXTRA = Action(0x1b, '''\
        RAISE(smite_extra(S));
    ''')

    PUSH_WORD_SIZE = Action(0x1c, '''\
        PUSH(smite_word_size);
    ''')

    PUSH_NATIVE_POINTER_SIZE = Action(0x1d, '''\
        PUSH(smite_native_pointer_size);
    ''')

    PUSH_FRAME_DEPTH = Action(0x1e, '''\
        smite_WORD value = S->FRAME_DEPTH;
        PUSH(value);
    ''')

    STORE_FRAME_DEPTH = Action(0x1f, '''\
        smite_WORD value;
        POP(&value);
        S->FRAME_DEPTH = value;
    ''')

    PUSH_PC = Action(0x20, '''\
        PUSH(S->PC);
    ''')

    PUSH_MEMORY = Action(0x21, '''\
        PUSH(S->MEMORY);
    ''')

    PUSH_F0 = Action(0x22, '''\
        PUSH(S->F0);
    ''')

    STORE_F0 = Action(0x23, '''\
        smite_WORD addr;
        POP(&addr);
        S->F0 = addr;
    ''')

    PUSH_FRAME = Action(0x24, '''\
        smite_WORD addr;
        POP(&addr);
        smite_WORD items;
        POP(&items);
        smite_UWORD old_F0 = S->F0;
        smite_UWORD old_FRAME_DEPTH = S->FRAME_DEPTH;
        S->F0 = old_F0 + old_FRAME_DEPTH - items + smite_frame_info_words;
        S->FRAME_DEPTH = items;
        RAISE(smite_copy_stack_address(S, old_F0 + old_FRAME_DEPTH - items, S->F0, items));
        RAISE(smite_store_stack_address(S, S->F0 - 2, addr));
        RAISE(smite_store_stack_address(S, S->F0 - 1, old_F0));
    ''')

    POP_FRAME = Action(0x25, '''\
        smite_WORD outer_F0;
        RAISE(smite_load_stack_address(S, S->F0 - 1, &outer_F0));
        smite_WORD outer_value;
        RAISE(smite_load_stack_address(S, S->F0 - 2, &outer_value));
        RAISE(smite_copy_stack_address(S, S->F0, S->F0 - smite_frame_info_words, S->FRAME_DEPTH));
        S->FRAME_DEPTH = S->F0 + S->FRAME_DEPTH - (smite_UWORD)outer_F0 - smite_frame_info_words;
        S->F0 = (smite_UWORD)outer_F0;
        PUSH(outer_value);
    ''')

    LOAD_FRAME_VALUE = Action(0x26, '''\
        smite_WORD frame;
        POP(&frame);
        smite_WORD outer_value;
        RAISE(smite_load_stack_address(S, frame - 2, &outer_value));
        PUSH(outer_value);
    ''')

    LOAD_OUTER_F0 = Action(0x27, '''\
        smite_WORD frame;
        POP(&frame);
        smite_WORD outer_F0;
        RAISE(smite_load_stack_address(S, frame - 1, &outer_F0));
        PUSH(outer_F0);
    ''')

    LOAD_OUTER_DEPTH = Action(0x28, '''\
        smite_WORD frame;
        POP(&frame);
        smite_WORD outer_F0;
        RAISE(smite_load_stack_address(S, frame - 1, &outer_F0));
        PUSH(frame - outer_F0 - smite_frame_info_words);
    ''')

    FRAME_DUP = Action(0x29, '''\
        smite_WORD frame;
        POP(&frame);
        smite_WORD depth;
        POP(&depth);
        smite_WORD dupee;
        RAISE(smite_load_stack_address(S, frame + depth, &dupee));
        PUSH(dupee);
    ''')

    FRAME_SWAP = Action(0x2a, '''\
        smite_WORD frame;
        POP(&frame);
        smite_WORD depth;
        POP(&depth);
        smite_WORD swapee;
        RAISE(smite_load_stack_address(S, frame + depth, &swapee));
        smite_WORD top;
        POP(&top);
        PUSH(swapee);
        RAISE(smite_store_stack_address(S, frame + depth, top));
    ''')

    CALL_FRAME = Action(0x2b, '''\
        /* FIXME: have a way to concatenate actions */
        /* CALL */
        {
            smite_WORD addr;
            POP(&addr);
            PUSH(S->PC);
            S->PC = addr;
        }
        /* PUSH_FRAME */
        {
            smite_WORD addr;
            POP(&addr);
            smite_WORD items;
            POP(&items);
            smite_UWORD old_F0 = S->F0;
            smite_UWORD old_FRAME_DEPTH = S->FRAME_DEPTH;
            S->F0 = old_F0 + old_FRAME_DEPTH - items + smite_frame_info_words;
            S->FRAME_DEPTH = items;
            RAISE(smite_copy_stack_address(S, old_F0 + old_FRAME_DEPTH - items, S->F0, items));
            RAISE(smite_store_stack_address(S, S->F0 - 2, addr));
            RAISE(smite_store_stack_address(S, S->F0 - 1, old_F0));
        }
    ''')
