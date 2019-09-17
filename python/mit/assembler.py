'''
Mit assembler/disassembler

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .binding import (
    align, is_aligned,
    word_bytes, word_bit, word_mask, sign_bit,
    opcode_bit, opcode_mask,
    hex0x_word_width,
)
from .enums import (
    Instruction, InternalExtraInstruction, LibInstruction,
    TERMINAL_OPCODES,
)


LIT = Instruction.LIT
LIT_PC_REL = Instruction.LIT_PC_REL
JUMP = Instruction.JUMP
CALL = Instruction.CALL

mnemonic = {
    instruction.value: instruction.name
    for instruction in Instruction
}
internal_extra_mnemonic = {
    instruction.value: instruction.name
    for instruction in InternalExtraInstruction
}
external_extra_mnemonic = {
    instruction.opcode: instruction.name
    for instruction in LibInstruction
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
            self.pc = self.state.registers["pc"].get()
            self.ir = self.state.registers["ir"].get()
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
        word = self.state.M_word[self.pc] & word_mask
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
                name = "undefined opcode {:#x}".format(opcode)
            if opcode == LIT or opcode == LIT_PC_REL:
                initial_pc = self.pc
                value = self._fetch()
                signed_value = value
                if value & sign_bit:
                    signed_value -= 1 << word_bit
                if opcode == LIT:
                    comment = ' ({:#x}={})'.format(value, signed_value)
                else: # opcode == LIT_PC_REL
                    comment = ' ({:#x})'.format(initial_pc + signed_value)
            if opcode in TERMINAL_OPCODES:
                # Call `self._fetch()` later, not now.
                if self.ir != 0:
                    comment = 'invalid extra instruction'
                    try:
                        if opcode == CALL:
                            comment = internal_extra_mnemonic[self.ir]
                        elif opcode == JUMP:
                            comment = external_extra_mnemonic[self.ir]
                    except KeyError:
                        pass
                    comment = ' ({})'.format(comment)
                self.ir = 0
        except IndexError:
            name = "invalid address!"
        return '{}{}'.format(name, comment)

    def __next__(self):
        pc_str = ('{:#0' + str(hex0x_word_width) + 'x}').format(self.pc)
        addr = '.' * len(pc_str)
        if self.ir == 0:
            self.ir = self._fetch()
            addr = pc_str
        return '{}: {}'.format(addr, self.disassemble())

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
            self.pc = self.state.registers["pc"].get()
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
        self.pc = align(self.pc)

    def _fetch(self):
        '''
        Start a new word.
        '''
        self.i_addr = self.pc
        self.word(0)
        self.i_shift = 0

    def instruction(self, opcode, extra_opcode=None):
        '''
        Appends an instruction opcode.

         - opcode - An Instruction or an `opcode_bit`-bit integer.
         - extra_opcode - optional - if `opcode` is `JUMP` or `CALL`, the
           extra opcode for an extra instruction.  This can be any type that
           can be converted to an int; it is typically an IntEnum value.
        '''
        # Compute the extended opcode.
        extended_opcode = int(opcode)
        assert 0 <= extended_opcode <= opcode_mask
        if extra_opcode is not None:
            assert extended_opcode in (CALL, JUMP)
            extended_opcode |= (int(extra_opcode) << opcode_bit)

        # Store the extended opcode, starting a new word if necessary.
        if self.i_addr is None:
            # Start of a new word.
            assert self.i_shift is None
            self._fetch()
        i = self.state.M_word[self.i_addr]
        i |= extended_opcode << self.i_shift
        i &= word_mask
        if (i >> self.i_shift) != extended_opcode:
            # Doesn't fit in the current word.
            self._fetch()
            i = extended_opcode
        self.state.M_word[self.i_addr] = i

        # If the opcode is terminal, start a new word.
        if opcode in TERMINAL_OPCODES:
            self.label()
        else:
            assert extended_opcode == int(opcode)
            self.i_shift += opcode_bit

    def lit(self, value):
        self.instruction(LIT)
        self.word(value)

    def lit_pc_rel(self, value):
        self.instruction(LIT_PC_REL)
        self.word(value - self.pc)

    def goto(self, pc):
        assert is_aligned(pc)
        self.pc = pc
        self.label()
