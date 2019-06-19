'''
Mit

This package provides Mit bindings for Python 3, and offers a convenient
set of functions and variables to interact with Mit in a Python REPL.
Module mit.assembler provides Assembler and Disassembler.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

When run as a script (Mit provides 'mit-shell' to do this), the module
provides a global Mit instance in VM, and defines various globals. See
`State.globalize()` for details.
'''

from .errors import MitErrorCode, MallocErrorCode, LoadErrorCode, SaveErrorCode
from .opcodes import (
    Register, Instruction, TERMINAL_OPCODES, InternalExtraInstruction,
    LibMit, LibC, LibInstruction,
)
from .binding import (
    Error, VMError,
    endism, word_bytes,
    size_word,
    byte_bit, byte_mask,
    word_bit, word_mask, sign_bit,
    opcode_bit, opcode_mask,
    c_uword, c_word,
    word_min, word_max, uword_max,
    align, is_aligned,
)
from .stack import Stack
from .memory import Memory, WordMemory
from .state import State
from .assembler import Assembler, Disassembler
