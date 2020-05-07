'''
Mit assembler/disassembler

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .binding import (
    is_aligned,
    word_bytes, word_bit, word_mask, sign_bit,
    opcode_bit, opcode_mask,
    hex0x_word_width,
)
from .enums import Instruction, ExtraInstruction, TERMINAL_OPCODES
from .trap_enums import LibInstruction

NEXT = Instruction.NEXT
JUMP = Instruction.JUMP
JUMPZ = Instruction.JUMPZ
CALL = Instruction.CALL
PUSH = Instruction.PUSH
PUSHI_0 = Instruction.PUSHI_0
PUSHREL = Instruction.PUSHREL
PUSHRELI_0 = Instruction.PUSHRELI_0
NEXTFF = Instruction.NEXTFF

mnemonic = {
    instruction.value: instruction.name
    for instruction in Instruction
}
extra_mnemonic = {
    instruction.value: instruction.name
    for instruction in ExtraInstruction
}


class Disassembler:
    '''
    Represents the state of a disassembler. This class simulates the pc and
    ir registers. When it reaches one of the TERMINAL_OPCODES, it
    continues at the next word. The `goto()` method sets a new disassembly
    address. Each call to `__next__()` dissassembles one instruction.

    Public fields:
     - pc - the value of the simulated pc register.
     - ir - the value of the simulated ir register.
     - end - the pc value at which to stop.
    '''
    def __init__(self, state, pc=None, length=None, end=None, ir=0):
        '''
        Disassembles code from the memory of `state`. `pc` and `ir`
        default to the current pc and ir values of `state`.
        `length` defaults to 32.
        '''
        self.state = state
        if pc is None:
            self.pc = self.state.pc
            self.ir = self.state.ir
            if self.ir & sign_bit:
                ir = ir | (-1 & ~word_mask)
        else:
            self.pc = pc
            self.ir = ir
        assert is_aligned(self.pc)
        self.end = end
        if length is not None:
            self.end = self.pc + length
        elif end is None:
            self.end = self.pc + 32

    def _fetch(self):
        if self.pc >= self.end:
            raise StopIteration
        word = self.state.M_word[self.pc]
        self.pc += word_bytes
        return word

    def __iter__(self):
        return self

    def disassemble(self):
        try:
            comment = ''
            opcode = self.ir & opcode_mask
            self.ir >>= opcode_bit
            try:
                name = mnemonic[opcode].lower()
            except KeyError:
                name = f"undefined opcode {opcode:#x}"
            if opcode == PUSH or opcode == PUSHREL:
                initial_pc = self.pc
                value = self._fetch()
                signed_value = value
                if value & sign_bit:
                    signed_value -= 1 << word_bit
                if opcode == PUSH:
                    comment = f' ({value:#x}={signed_value})'
                else: # opcode == PUSHREL
                    comment = f' ({initial_pc + signed_value:#x})'
            elif opcode & 1 == 1 and opcode != NEXTFF: # PUSHRELI
                value = (opcode - PUSHRELI_0) >> 1
                if opcode & 0x80:
                    value |= -1 & ~0x7f
                comment = f' ({self.pc + value * word_bytes:#x})'
            elif opcode == NEXT and self.ir != 0:
                # Call `self._fetch()` later, not now.
                comment = extra_mnemonic.get(
                    self.ir,
                    f'invalid extra instruction {self.ir:#x}'
                )
                comment = f' ({comment})'
                self.ir = 0
            elif opcode in (JUMP, JUMPZ, CALL) and self.ir != 0:
                # Call `self._fetch()` later, not now.
                comment = f' (to {self.pc + self.ir * word_bytes:#x})'
                self.ir = 0
        except IndexError:
            name = "invalid address!"
        return f'{name}{comment}'

    def __next__(self):
        pc_str = ('{:#0' + str(hex0x_word_width) + 'x}').format(self.pc)
        addr = '.' * len(pc_str)
        if self.ir == 0:
            self.ir = self._fetch()
            addr = pc_str
        return f'{addr}: {self.disassemble()}'

    def goto(self, pc):
        '''
        After calling this method, disassembly will start from `pc`.
        '''
        assert is_aligned(self.pc)
        self.pc = pc
        self.ir = 0


class Assembler:
    '''
    Represents the state of an assembler.

    Public fields:
     - pc - the value of the simulated pc register.
     - i_addr - the address of the latest opcode word, i.e. the word from
       which the simulated ir register was most recently loaded.
       `None` indicates that we're about to start a new word.
     - i_shift - the number of opcode bits already in the word at `i_addr`,
       or `None`.
    '''
    def __init__(self, state, pc=None):
        '''
        `pc` defaults to the current pc value of `state`.
        '''
        self.state = state
        if pc is None:
            self.pc = self.state.pc
        else:
            self.pc = pc
        assert is_aligned(self.pc)
        self.label()

    def label(self):
        '''
        Skips to the start of a word, and returns its address.
        '''
        self.i_addr = None
        self.i_shift = None
        return self.pc

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
        assert self.i_addr is None
        for b in bytes:
            self.state.M[self.pc] = b
            self.pc += 1
        # Align `pc`
        self.pc = ((self.pc - 1) & word_mask) + word_bytes

    def _fetch(self):
        '''
        Start a new word.
        '''
        self.i_addr = self.pc
        self.word(0)
        self.i_shift = 0

    def fit(self, extended_opcode):
        '''
        Determine whether the given extended opcode fits in the current word.
        If so, return the updated word; otherwise, None.
        '''
        i = self.state.M_word[self.i_addr or self.pc]
        i_shift = self.i_shift or 0
        i |= extended_opcode << i_shift
        i &= word_mask
        sign_mask = (-1 if extended_opcode < 0 else 0) & (~word_mask)
        if (i | sign_mask) >> i_shift == extended_opcode:
            return i
        return None

    def instruction(self, opcode, extra_opcode=None):
        '''
        Appends an instruction opcode.

         - opcode - An Instruction or an `opcode_bit`-bit integer.
         - extra_opcode - int - if `opcode` is `NEXT`, `JUMP`, `JUMPZ` or
           `CALL`, the rest of the instruction word.
        '''
        # Compute the extended opcode.
        extended_opcode = int(opcode)
        assert 0 <= extended_opcode <= opcode_mask
        if extra_opcode is not None:
            assert extended_opcode in (NEXT, JUMP, JUMPZ, CALL)
            extended_opcode |= (int(extra_opcode) << opcode_bit)

        # Store the extended opcode, starting a new word if necessary.
        if self.i_addr is None:
            # Start of a new word.
            assert self.i_shift is None
            self._fetch()
        i = self.fit(extended_opcode)
        if i is None: # Doesn't fit in the current word.
            self._fetch()
            i = extended_opcode
        self.state.M_word[self.i_addr] = i

        # If the opcode is terminal, start a new word.
        if opcode in TERMINAL_OPCODES:
            self.label()
        else:
            assert extended_opcode == int(opcode)
            self.i_shift += opcode_bit

    def jump_rel(self, addr, opcode=JUMP):
        '''
        Assemble a relative `jump`, `jumpz` or `call` instruction to the given
        address. Selects the immediate form of the instruction if possible.
        '''
        assert opcode in (JUMP, JUMPZ, CALL)
        assert is_aligned(addr)
        word_offset = (addr - self.pc - word_bytes) // word_bytes
        assert word_offset != 0, "immediate branch offset cannot be 0"
        if self.fit(int(opcode) | (word_offset << opcode_bit)):
            self.instruction(opcode, word_offset)
        else:
            self.lit_pc_rel(addr)
            self.instruction(opcode)

    def lit(self, value, force_long=False):
        '''
        Assemble a `push` instruction that pushes the specified `value`.
        Uses `pushi` if possible and `!force_long`.
        '''
        value = int(value)
        if not force_long and -32 <= value < 32:
            self.instruction((PUSHI_0 + (value << 2)) & opcode_mask)
        else:
            self.instruction(PUSH)
            self.word(value)

    def lit_pc_rel(self, address, force_long=False):
        '''
        Assemble a `pushrel` instruction that pushes the specified `address`.
        Uses `pushreli` if possible and `!force_long`.
        '''
        address = int(address)
        offset = address - self.pc
        if self.i_addr == None:
            offset -= word_bytes
        offset_words = offset // word_bytes
        if not force_long and offset_words != -1 and -64 <= offset_words < 64:
            self.instruction((PUSHRELI_0 + (offset_words << 1)) & opcode_mask)
        else:
            self.instruction(PUSHREL)
            self.word(offset)

    def goto(self, pc):
        assert is_aligned(pc)
        self.pc = pc
        self.label()
