'''
Mit disassembler.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .binding import (
    is_aligned, sign_extend,
    word_bytes, word_bit, uword_max, sign_bit,
    hex0x_word_width,
)
from .enums import Instructions, Instructions as I, ExtraInstructions


mnemonic = {
    instruction.value: instruction.name
    for instruction in Instructions
}
extra_mnemonic = {
    instruction.value: instruction.name
    for instruction in ExtraInstructions
}


class Disassembler:
    '''
    Represents the state of a disassembler. This class simulates the pc and
    ir registers. When it reaches a terminal instruction, it continues at
    the next word. The `goto()` method sets a new disassembly address. Each
    call to `__next__()` dissassembles one instruction.

    Public fields:
     - pc - the value of the simulated pc register.
     - ir - the value of the simulated ir register.
     - end - the pc value at which to stop.
    '''
    def __init__(self, state, pc=None, length=None, end=None, ir=0):
        '''
        Disassembles code from the memory of `state`. `pc` and `ir`
        default to the current pc and ir values of `state`.
        `length` is in words, and defaults to 16.
        '''
        self.state = state
        self.pc = self.state.pc if pc is None else pc
        self.ir = ir
        assert is_aligned(self.pc)
        self.end = end
        if length is None and end is None:
            length = 16
        if length is not None:
            self.end = self.pc + length * word_bytes

    def _fetch(self):
        if self.pc >= self.end:
            raise StopIteration
        word = sign_extend(self.state.M_word[self.pc])
        self.pc += word_bytes
        return word

    def __iter__(self):
        return self

    def disassemble(self):
        try:
            comment = ''
            opcode = self.ir & 0xff
            self.ir >>= 8
            try:
                name = mnemonic[opcode].lower()
            except KeyError:
                name = f"undefined opcode {opcode:#x}"
            if opcode in (I.PUSH, I.PUSHREL):
                initial_pc = self.pc
                value = self._fetch()
                unsigned_value = value & uword_max
                if opcode == I.PUSH:
                    comment = f' ({unsigned_value:#x}={value})'
                else: # opcode == I.PUSHREL
                    comment = f' ({(initial_pc + value) & uword_max:#x})'
            elif opcode & 1 == 1 and opcode != I.NEXTFF: # PUSHRELI_N
                value = (opcode - I.PUSHRELI_0) >> 1
                if opcode & 0x80:
                    value |= -1 & ~0x7f
                comment = f' ({self.pc + value * word_bytes:#x})'
            elif opcode == I.NEXT and self.ir != 0:
                # Call `self._fetch()` later, not now.
                comment = extra_mnemonic.get(
                    self.ir,
                    f'invalid extra instruction {self.ir:#x}'
                )
                comment = f' ({comment})'
                self.ir = 0
            elif opcode == I.NEXTFF:
                # Call `self._fetch()` later, not now.
                if self.ir != -1:
                    comment = f' (trap {self.ir:#x})'
                self.ir = 0
            elif opcode in (I.JUMP, I.JUMPZ, I.CALL) and self.ir != 0:
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
