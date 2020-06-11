'''
Mit assembler.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .binding import (
    is_aligned, sign_extend,
    word_bit, word_bytes, uword_max,
)
from .enums import Instructions as I, TERMINAL_OPCODES


class Assembler:
    '''
    Represents the state of an assembler.

    Public fields:
     - pc - the value of the simulated pc register.
     - i_addr - the address of the latest opcode word, i.e. the word from
       which the simulated ir register was most recently loaded.
     - i_shift - the number of opcode bits already in the word at `i_addr`.
    '''
    def __init__(self, state, pc=None):
        '''
        `pc` defaults to the current pc value of `state`.
        '''
        self.state = state
        self.pc = pc
        if pc is None:
            self.pc = self.state.pc
        assert is_aligned(self.pc)
        self.label()

    def label(self):
        '''
        Skips to the start of a word, and returns its address.
        '''
        self.i_addr = self.pc
        self.i_shift = 0
        return self.pc

    def goto(self, pc):
        assert is_aligned(pc)
        self.pc = pc
        self.label()

    def word(self, value):
        '''
        Writes a word with value `value` at `pc` and increments `pc`.
        '''
        self.state.M_word[self.pc] = value
        self.pc += word_bytes

    def bytes(self, bytes):
        '''
        Writes `bytes` at `pc`, followed by padding to the next word.
        '''
        assert self.i_shift == 0
        for b in bytes:
            self.state.M[self.pc] = b
            self.pc += 1
        # Align `pc`
        self.pc = ((self.pc - 1) & (word_bytes - 1)) + word_bytes

    def fit(self, opcode, operand):
        '''
        Determine whether the given extended opcode fits in the current word.
        If so, return the updated word; otherwise, None.
        '''
        opcode = int(opcode)
        if operand is not None:
            operand = int(operand)
        i = sign_extend(self.state.M_word[self.i_addr])
        i |= (opcode << self.i_shift) | ((operand or 0) << (self.i_shift + 8))
        i &= uword_max
        i = sign_extend(i)
        if ((i >> self.i_shift) & 0xff == opcode and
            (operand is None or i >> (self.i_shift + 8) == operand)
        ):
            return i
        return None

    def instruction(self, opcode, operand=None):
        '''
        Appends an instruction opcode.

         - opcode - An Instruction or an 8-bit integer.
         - operand - int - if `opcode` is `NEXT`, `JUMP`, `JUMPZ` or
           `CALL`, the rest of the instruction word.
        '''
        # Compute the extended opcode.
        opcode = int(opcode)
        assert 0 <= opcode <= 0xff
        if operand is not None:
            assert opcode in TERMINAL_OPCODES

        # Start a new word if we need to.
        if self.i_shift == 0:
            self.i_addr = self.pc
            self.word(0)

        # Store the extended opcode, starting a new word if necessary.
        i = self.fit(opcode, operand)
        if i is None: # Doesn't fit in the current word.
            self.label()
            self.word(0)
            i = self.fit(opcode, operand)
            assert i
        self.state.M_word[self.i_addr] = i

        # Advance `self.i_shift` past used bits.
        self.i_shift += 8
        if opcode in TERMINAL_OPCODES:
            self.i_shift = word_bit

        # If we finished a word, move to next.
        if self.i_shift == word_bit:
            self.label()

    def jump_rel(self, addr, opcode=I.JUMP):
        '''
        Assemble a relative `jump`, `jumpz` or `call` instruction to the given
        address. Selects the immediate form of the instruction if possible.
        '''
        assert opcode in (I.JUMP, I.JUMPZ, I.CALL)
        assert is_aligned(addr)
        # Compute value of `pc` that will be added to offset.
        effective_pc = self.pc
        if self.i_shift == 0:
            effective_pc += word_bytes
        word_offset = (addr - effective_pc) // word_bytes
        if word_offset != 0 and word_offset != -1 and self.fit(opcode, word_offset):
            self.instruction(opcode, word_offset)
        else:
            self.lit_pc_rel(addr)
            self.instruction(opcode)

    def lit(self, value, force_long=False):
        '''
        Assemble a `push` instruction that pushes the specified `value`.
        Uses `pushi` if possible and `force_long` is false.
        '''
        value = int(value)
        if not force_long and -32 <= value < 32:
            self.instruction((I.PUSHI_0 + (value << 2)) & 0xff)
        else:
            self.instruction(I.PUSH)
            self.word(value)

    def lit_pc_rel(self, address, force_long=False):
        '''
        Assemble a `pushrel` instruction that pushes the specified `address`.
        Uses `pushreli` if possible and `force_long` is false.
        '''
        address = int(address)
        offset = address - self.pc
        if self.i_shift == 0:
            offset -= word_bytes
        offset_words = offset // word_bytes
        if not force_long and offset_words != -1 and -64 <= offset_words < 64:
            self.instruction((I.PUSHRELI_0 + (offset_words << 1)) & 0xff)
        else:
            self.instruction(I.PUSHREL)
            self.word(offset)

    def extra(self, extra_opcode):
        self.instruction(I.NEXT, extra_opcode)

    def trap(self, extra_opcode):
        self.instruction(I.NEXTFF, extra_opcode)
