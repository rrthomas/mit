'''
Convenient globals.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

Defines a default State, and makes it accessible through global
variables and functions:

 - The State itself: VM
 - Managing the VM state: load, save
 - Controlling and observing execution: run, step, trace
 - Memory: M[], M_word[], dump, dump_files
 - Assembly: Assembler, Disassembler, assembler,
   label, goto, instruction, jumprel, push, pushrel, extra, trap
 - Abbreviations: ass=assembler.instruction, dis=VM.disassemble
 - The instruction opcodes are available as constants.
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
vars().update({
    name: assembler.__getattribute__(name)
    for name in [
        "label", "goto", "instruction",
        "jumprel", "push", "pushrel", "extra", "trap",
    ]
})


def trace(*args, **kwargs):
    'A convenience wrapper for `State.step(trace=True)`.'
    VM.step(*args, trace=True, **kwargs)


# Change the default length of `save()`.
def save(file, addr=None, length=None):
    '''
    Save a binary image of part of `M`. Works like `State.save()` but if `addr`
    and `length` are omitted it will save up to `assembler.pc`.
    '''
    if addr is None and length is None:
        assert is_aligned(assembler.pc)
        length = assembler.pc - VM.M.addr
    VM.save(file, addr, length // word_bytes)

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
