'''
Python bindings for libmit.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from ctypes import (
    c_char_p, c_void_p,
    c_int,
    c_size_t, c_ssize_t,
    sizeof, pointer, POINTER, CFUNCTYPE, CDLL,
)
from ctypes.util import find_library

from .enums import MitErrorCode, Registers


library_file = find_library("mit")
if not library_file:
    # For Windows
    # TODO: Do this portably
    # TODO: Substitute version when library is versioned
    library_file = find_library("libmit-0")
assert(library_file)
libmit = CDLL(library_file)
assert(libmit)

# Errors
class Error(Exception):
    '''
    An error from the Python bindings for Mit.
    '''
    pass

class VMError(Error):
    '''
    An error from Mit.

    Public fields:
     - error_code - int
     - message - str
    '''
    def __init__(self, error_code, message):
        super().__init__(error_code, message)

def errcheck(error_enum):
    '''
    Returns a callback suitable for use as `ctypes._FuncPtr.errcheck`.
     - code_to_message - a mapping from int to message. If the message is
       `None` the code is considered to be a success, and `None` is returned.
       If the code is not found in `code_to_message`:
        - if an "ok" code exists, an "unknown error" is reported.
        - otherwise the result is returned unchanged.
    '''
    code_to_message = {error.value: error.name.lower().translate(str.maketrans('_', ' '))
                       for error in error_enum}
    require_match = 'ok' in code_to_message.values()
    def callback(result, _func=None, _args=None):
        result = int(result)
        if result in code_to_message:
            message = code_to_message[result]
            if message == 'ok':
                return
        elif require_match:
            message = "unknown error!"
        else:
            return result
        raise VMError(result, message)
    return callback


# Types
c_word = c_ssize_t
c_uword = c_size_t
c_mit_fn = CFUNCTYPE(
    c_word,
    POINTER(c_word), c_word, POINTER(c_word), c_uword, POINTER(c_uword),
)

# Constants
word_bytes = sizeof(c_uword)
assert word_bytes in (4, 8), f"word_bytes must be 4 or 8 and is {word_bytes}!"
word_bit = word_bytes * 8
sign_bit = 1 << (word_bit - 1)
hex0x_word_width = word_bytes * 2 + 2 # Width of a hex word with leading "0x"
uword_max = c_uword(-1).value


# Functions from mit.h

# Errors
mit_error = errcheck(MitErrorCode)

# Bind `mit_run` as a function and as a function pointer, because
# for some reason we can't call it when bound as a pointer.
_run = c_mit_fn.in_dll(libmit, "mit_run")
run_ptr = POINTER(c_mit_fn).in_dll(libmit, "mit_run")
# `break_fn_ptr` must be bound as a `c_void_p` in order to be set to point
# to a Python callback.
break_fn_ptr = c_void_p.in_dll(libmit, "mit_break_fn")
stack_words_ptr = pointer(c_uword.in_dll(libmit, "mit_stack_words"))
stack_words = c_uword.in_dll(libmit, "mit_stack_words")
run_simple = c_mit_fn.in_dll(libmit, "mit_run_simple")
run_break = c_mit_fn.in_dll(libmit, "mit_run_break")
#run_fast = c_mit_fn.in_dll(libmit, "mit_run_fast")
#run_profile = c_mit_fn.in_dll(libmit, "mit_run_profile")

# Cannot add errcheck to a CFUNCTYPE, so wrap it manually.
def run(pc, ir, stack, stack_words, stack_depth_ptr):
    return mit_error(_run(pc, ir, stack, stack_words, stack_depth_ptr))

# libmit.mit_profile_reset.restype = None
# libmit.mit_profile_reset.argtypes = None

# libmit.mit_profile_dump.argtypes = [c_int]

def is_aligned(addr):
    return (addr & (word_bytes - 1)) == 0

def sign_extend(x):
    if x & sign_bit:
        x |= -1 & ~uword_max
    return x

argc = c_int.in_dll(libmit, "mit_argc")
argv = POINTER(c_char_p).in_dll(libmit, "mit_argv")

def register_args(*args):
    '''
    Set `mit_argc` and `mit_argv`.

     - args - an iterable of `str` and/or `bytes`.
    '''
    bargs = []
    for arg in args:
        if isinstance(arg, str):
            arg = bytes(arg, 'utf-8')
        assert isinstance(arg, bytes)
        bargs.append(arg)
    global argc, argv
    argc.value = len(bargs)
    argv.contents = (c_char_p * len(bargs))(*bargs)
