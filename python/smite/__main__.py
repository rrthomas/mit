import inspect

from . import *

def init():
    VM = State()
    frm = inspect.stack()[1]
    # Make some handy globals for interactive use
    frm[0].f_globals["VM"] = VM
    VM.globalize(frm[0].f_globals)

init()