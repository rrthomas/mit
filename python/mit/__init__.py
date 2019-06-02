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

from .state import *
from .memory import *
from .stack import *
from .opcodes import *
from .binding import *
from .assembler import *
