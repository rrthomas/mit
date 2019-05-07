'''
Python shell for Mit.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import inspect

from . import *

def init():
    VM = State()
    frm = inspect.stack()[1]
    # Make some handy globals for interactive use
    frm[0].f_globals["VM"] = VM
    VM.globalize(frm[0].f_globals)

init()