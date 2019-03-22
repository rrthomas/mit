'''SMite assembler/disassembler'''

from .binding import *
from .vm_data import Instructions
from .vm_data_extra import LibInstructions

LIT = Instructions.LIT.value.opcode
LIT_PC_REL = Instructions.LIT_PC_REL.value.opcode
BRANCH = Instructions.BRANCH.value.opcode
CALL = Instructions.CALL.value.opcode

mnemonic = {
    instruction.value.opcode: instruction.name
    for instruction in Instructions
}
mnemonic.update({
    instruction.value.opcode: instruction.name
    for instruction in LibInstructions
})

# The set of opcodes which must be the last in a word.
TERMINAL_OPCODES = frozenset([0, BRANCH, CALL])

# FIXME: add enumerate support, so we can co-iterate over PC and
# disassembled instruction.
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
        self.pc += word_size
        return word

    def __iter__(self):
        return self

    def disassemble(self):
        try:
            comment = ''
            opcode = self.i & INSTRUCTION_MASK
            self.i >>= INSTRUCTION_BITS
            try:
                name = mnemonic[opcode]
            except KeyError:
                name = 'undefined!'
            if opcode == LIT or opcode == LIT_PC_REL:
                initial_pc = self.pc
                value = self._fetch()
                signed_value = value
                if value & SIGN_BIT:
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
        self.pc += word_size

    def _fetch(self):
        '''
        Start a new word.
        '''
        self.i_addr = self.pc
        self.word(0)
        self.i_shift = 0

    def instruction(self, opcode):
        '''
        Appends an instruction opcode. If possible, this will be put in the
        same word as the previous opcode, otherwise it will start a new word.
        '''
        assert 0 <= opcode <= INSTRUCTION_MASK
        if self.i_addr is None:
            # Start of a new word.
            assert self.i_shift is None
            self._fetch()
        i = self.state.M_word[self.i_addr]
        i |= opcode << self.i_shift
        i &= word_mask
        if (i >> self.i_shift) != opcode:
            # Doesn't fit in the current word.
            self._fetch()
            i = opcode
        self.state.M_word[self.i_addr] = i
        self.i_shift += INSTRUCTION_BITS
        if opcode in TERMINAL_OPCODES:
            self.label()

    def lit(self, value):
        self.instruction(LIT)
        self.word(value)

    def lit_pc_rel(self, value):
        self.instruction(LIT_PC_REL)
        self.word(value - self.pc)

    def lit_bytes(self, *values):
        aligned_size = libsmite.smite_align(len(values))
        values += (0,) * (aligned_size - len(values))
        for i in range(libsmite.smite_align(len(values)) // word_size):
            word = 0
            for j in reversed(range(word_size)):
                word = (word << byte_bit) | values[i * word_size + j]
            self.word(word)

    def goto(self, pc):
        assert is_aligned(pc)
        self.pc = pc
        self.label()