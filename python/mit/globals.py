'''
Convenient globals.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

Make the state accessible through global variables and functions.

Returns a vars table containing:

Managing the VM state: load, save
Controlling and observing execution: run, step, trace
Memory: M[], M_word[], dump, dump_files
Assembly: Assembler, Disassembler, assembler,
    word, bytes, instruction, lit, lit_pc_rel, label, goto
Abbreviations: ass=assembler.instruction, dis=self.disassemble

The instruction opcodes are available as constants.
'''

from . import *


VM = State()

# Bits of the VM.
vars().update({
    name: VM.__getattribute__(name)
    for name in [
        "M", "M_word", "S",
        "load", "run", "step", "trace",
        "dump", "disassemble", "dump_files",
    ]
})

# An Assembler.
assembler = Assembler(VM)
vars()['assembler'] = assembler
vars().update({
    name: assembler.__getattribute__(name)
    for name in [
        "instruction", "jump_rel", "lit", "lit_pc_rel",
        "label", "goto"
    ]
})

# Add a default length to `save()`.
def _save(file, addr=None, length=None):
    if addr is None and length is None:
        length = assembler.pc - VM.M.addr
    VM.save(file, addr, length // word_bytes)
vars()['save'] = _save

# Abbreviations and disambiguations
ass_word = assembler.word
ass_bytes = assembler.bytes
ass = assembler.instruction
dis = disassemble

# Opcodes
vars().update(Instruction.__members__)
vars().update(ExtraInstruction.__members__)
vars().update(LibInstruction.__members__)
vars().update({
    lib.library.__name__: lib.library
    for lib in LibInstruction
})
