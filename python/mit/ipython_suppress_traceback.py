# IPython extension: suppress traceback
# From https://stackoverflow.com/questions/46222753/how-do-i-suppress-tracebacks-in-jupyter

import sys


def hide_traceback(exc_tuple=None, filename=None, tb_offset=None,
                   exception_only=False, running_compiled_code=False):
    etype, value, tb = sys.exc_info()
    return _ipython._showtraceback(etype, value, _ipython.InteractiveTB.get_exception_only(etype, value))


def load_ipython_extension(ipython):
    global _ipython
    _ipython = ipython
    ipython.showtraceback = hide_traceback
