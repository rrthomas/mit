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
    label, goto, instruction, jumprel, push, pushrel, extra, trap
Abbreviations: ass=assembler.instruction, dis=self.disassemble

The instruction opcodes are available as constants.
'''

from . import *


VM = State()

# Bits of the VM.
vars().update({
    name: VM.__getattribute__(name)
    for name in [
        "M", "M_word",
        "load", "run", "step",
        "dump", "disassemble", "dump_files",
    ]
})

# An Assembler.
assembler = Assembler(VM)
vars()['assembler'] = assembler
vars().update({
    name: assembler.__getattribute__(name)
    for name in [
        "label", "goto", "instruction",
        "jumprel", "push", "pushrel", "extra", "trap",
    ]
})

def trace(**kwargs):
    'A convenience wrapper for `step(trace=True)`.'
    VM.step(trace=True, **kwargs)

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
vars().update(Instructions.__members__)
vars().update(ExtraInstructions.__members__)
vars().update(LibInstructions.__members__)
vars().update({
    lib.library.__name__: lib.library
    for lib in LibInstructions
})
