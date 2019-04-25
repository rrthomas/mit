'''
SMite assembler/disassembler

(c) SMite authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .binding import (
    align, is_aligned,
    word_bytes, word_bit, word_mask, instruction_bit, instruction_mask, sign_bit,
)
from .vm_data import Instructions
from .ext import LibInstructions

LIT = Instructions.LIT.value.opcode
LIT_PC_REL = Instructions.LIT_PC_REL.value.opcode
BRANCH = Instructions.BRANCH.value.opcode
CALL = Instructions.CALL.value.opcode
HALT = Instructions.HALT.value.opcode

mnemonic = {
    instruction.value.opcode: instruction.name
    for instruction in Instructions
}
# FIXME: Disassemble LibInstructions when the literal directly precedes EXT
# mnemonic.update({
#     instruction.value.opcode: instruction.name
#     for instruction in LibInstructions
# })

# The set of opcodes which must be the last in a word.
TERMINAL_OPCODES = frozenset([0, BRANCH, CALL, HALT])

class Disassembler:
    '''
    Represents the state of a disassembler. This class simulates the PC and I
    registers. When it reaches one of the TERMINAL_OPCODES, it continues at
    the next word. The `goto()` method sets a new disassembly address.
    Each call to `__next__()` dissassembles one instruction.

    Public fields:
     - pc - the value of the simulated PC register.
     - i - the value of the simulated I register.
     - end - the PC value at which to stop.
    '''
    def __init__(self, state, pc=None, length=None, end=None, i=0):
        '''
        Disassembles code from the memory of `state`. `pc` and `i` default to
        the current PC and I values of `state`. `length` defaults to 32.
        '''
        self.state = state
        if pc is None:
            self.pc = self.state.registers["PC"].get()
            self.i = self.state.registers["I"].get()
        else:
            self.pc = pc
            self.i = i
        assert is_aligned(self.pc)
        self.end = end
        if length != None:
            self.end = self.pc + length
        elif end == None:
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
            opcode = self.i & instruction_mask
            self.i >>= instruction_bit
            try:
                name = mnemonic[opcode]
            except KeyError:
                name = 'undefined!'
            if opcode == LIT or opcode == LIT_PC_REL:
                initial_pc = self.pc
                value = self._fetch()
                signed_value = value
                if value & sign_bit:
                    signed_value -= 1 << word_bit
                if opcode == LIT:
                    comment = ' ({:#x}={})'.format(value, signed_value)
                else: # LIT_PC_REL
                    comment = ' ({:#x})'.format(initial_pc + signed_value)
            if opcode in TERMINAL_OPCODES:
                # Call `self._fetch()` later, not now.
                self.i = 0
        except IndexError:
            name = "invalid address!"
        except KeyError:
            name = "undefined opcode {:#x}" % opcode
        return '{}{}'.format(name, comment)

    def __next__(self):
        pc_str = '{:#x}'.format(self.pc)
        addr = '.' * len(pc_str)
        if self.i == 0:
            self.i = self._fetch()
            addr = pc_str
        return '{}: {}'.format(addr, self.disassemble())

    def goto(self, pc):
        '''
        After calling this method, disassembly will start from `pc`.
        '''
        assert is_aligned(self.pc)
        self.pc = pc
        self.i = 0

class Assembler:
    '''
    Represents the state of an assembler.

    Public fields:
     - pc - the value of the simulated PC register.
     - i_addr - the address of the latest opcode word, i.e. the word from
       which the simulated I register was most recently loaded. `None`
       indicates that we're about to start a new word.
     - i_shift - the number of opcode bits already in the word at `i_addr`,
       or `None`.
    '''
    def __init__(self, state, pc=None):
        '''
        `pc` defaults to the current PC value of `state`.
        '''
        self.state = state
        if pc is None:
            self.pc = self.state.registers["PC"].get()
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
        Inserts a word with value `value`.
        '''
        self.state.M_word[self.pc] = value
        self.pc += word_bytes

    def bytes(self, bytes):
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

    def effective_pc(self):
        '''
        Return address PC will have after executing the most recently assembled
        instruction.
        '''
        pc = self.pc
        if self.i_addr is None:
            pc += word_bytes
        return pc

    def instruction(self, opcode):
        '''
        Appends an instruction opcode into the current word, and advance pc if
        the current word is filled up.
        '''
        assert 0 <= opcode <= instruction_mask
        if self.i_addr is None:
            # Start of a new word.
            assert self.i_shift is None
            self._fetch()
        i = self.state.M_word[self.i_addr]
        i = (i | (opcode << self.i_shift)) & word_mask
        self.state.M_word[self.i_addr] = i
        self.i_shift += instruction_bit
        # If current word is full or we’ve assembled a terminal instruction,
        # advance pc
        if (self.i_shift > word_bit - instruction_bit or
            opcode in TERMINAL_OPCODES):
            self.label()

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
