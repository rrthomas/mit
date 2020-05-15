'''
Mit

This package provides Mit bindings for Python 3, and offers a convenient
set of functions and variables to interact with Mit in a Python REPL.
Module mit provides a Pythonic API.
Module mit.binding provides direct access to libmit.
Module mit.assembler provides Assembler
Module mit.disassembler provides Disassembler
Module mit.globals provides a convenient set of globals for interactive use
and for testing.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.

When run as a script (Mit provides 'mit-shell' to do this), the module
provides a global Mit instance in VM, and defines various globals. See
`State.globalize()` for details.
'''

from .enums import (
    Registers, Instructions, TERMINAL_OPCODES, ExtraInstructions,
    MitErrorCode
)
from .trap_enums import LibC, LibInstructions
from .binding import (
    Error, VMError,
    word_bytes,
    byte_bit, byte_mask,
    word_bit, word_mask, sign_bit,
    opcode_bit, opcode_mask,
    c_uword, c_word,
    word_min, word_max, uword_max,
    is_aligned, register_args,
)
from .state import State
from .assembler import Assembler
from .disassembler import Disassembler
