'''
Python bindings for libmit.

(c) Mit authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from ctypes import (
    c_ubyte, c_char_p,
    c_uint, c_int,
    c_uint16, c_int16,
    c_uint32, c_int32,
    c_uint64, c_int64,
    c_size_t,
    POINTER, CFUNCTYPE, CDLL, Structure,
)
from ctypes.util import find_library

from .enums import MitErrorCode, Register


library_file = find_library("mit")
features_library_file = find_library("mitfeatures")
if not library_file:
    # For Windows
    # TODO: Do this portably
    # TODO: Substitute version when library is versioned
    library_file = find_library("libmit-0")
    features_library_file = find_library("libmitfeatures-0")
assert(library_file)
assert(features_library_file)
libmit = CDLL(library_file)
assert(libmit)
libmitfeatures = CDLL(features_library_file)
assert(libmitfeatures)


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
     - code_to_message - a dict from int to message. If the message is `None`
       the code is considered to be a success, and `None` is returned.
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


# Constants (all of type unsigned)
vars().update([(c, c_uint.in_dll(libmit, "mit_{}".format(c)).value)
               for c in [
                       "word_bytes", "size_word",
                       "byte_bit", "byte_mask", "word_bit",
                       "opcode_bit", "opcode_mask",
               ]])
sign_bit = 1 << (word_bit - 1)
hex0x_word_width = word_bytes * 2 + 2 # Width of a hex word with leading "0x"


# Types
if word_bytes == 4:
    c_word = c_int32
    c_uword = c_uint32
elif word_bytes == 8:
    c_word = c_int64
    c_uword = c_uint64
else:
    raise Exception("Could not make Python C type matching WORD (size {})".format(word_bytes))

mit_state_fields = [
    (register.name, c_uword)
    for register in Register
]
mit_state_fields.extend([
    ('stack', POINTER(c_word)),
])
class c_mit_state(Structure):
    _fields_ = mit_state_fields

c_mit_fn = CFUNCTYPE(c_word, POINTER(c_mit_state))


# Constants that require VM types
vars().update([(c, cty.in_dll(libmit, "mit_{}".format(c)).value)
               for (c, cty) in [
                       ("word_mask", c_uword),
                       ("uword_max", c_uword),
                       ("word_min", c_word),
                       ("word_max", c_word),
               ]])


# Functions

# Errors
mit_error = errcheck(MitErrorCode)

# mit.h

# Bind mit_run as a function and as a function pointer, because
# for some reason we can't call it when bound as a pointer.
vars()["_run"] = c_mit_fn.in_dll(libmit, "mit_run")
vars()["run_ptr"] = POINTER(c_mit_fn).in_dll(libmit, "mit_run")
# Cannot add errcheck to a CFUNCTYPE, so wrap it manually.
def run(state):
    return mit_error(_run(state))

libmit.mit_load_stack.argtypes = [POINTER(c_mit_state), c_uword, POINTER(c_word)]
libmit.mit_load_stack.errcheck = mit_error
libmit.mit_store_stack.argtypes = [POINTER(c_mit_state), c_uword, c_word]
libmit.mit_store_stack.errcheck = mit_error
libmit.mit_pop_stack.argtypes = [POINTER(c_mit_state), POINTER(c_word)]
libmit.mit_pop_stack.errcheck = mit_error
libmit.mit_push_stack.argtypes = [POINTER(c_mit_state), c_word]
libmit.mit_push_stack.errcheck = mit_error

libmit.mit_single_step.restype = c_word
libmit.mit_single_step.argtypes = [POINTER(c_mit_state)]
libmit.mit_single_step.errcheck = mit_error

libmit.mit_new_state.restype = POINTER(c_mit_state)
libmit.mit_new_state.argtypes = [c_size_t]

libmit.mit_free_state.restype = None
libmit.mit_free_state.argtypes = [POINTER(c_mit_state)]

def is_aligned(addr):
    return (addr & ((1 << size_word) - 1)) == 0

# features.h
vars().update([(c, cty.in_dll(libmitfeatures, "mit_{}".format(c)))
               for (c, cty) in [
                       ("argc", c_int),
                       ("argv", POINTER(c_char_p)),
                       ("run_specializer", c_mit_fn),
                       ("run_profile", c_mit_fn),
               ]])

def register_args(*args):
    arg_strings = c_char_p * len(args)
    bargs = []
    for arg in args:
        if type(arg) == str:
            arg = bytes(arg, 'utf-8')
        elif type(arg) == int:
            arg = bytes(arg)
        bargs.append(arg)
    global argc, argv
    argv.contents = arg_strings(*bargs)
    argc.value = len(bargs)

libmitfeatures.mit_extra_instruction.restype = c_word
libmitfeatures.mit_extra_instruction.argtypes = [POINTER(c_mit_state)]
libmitfeatures.mit_extra_instruction.errcheck = mit_error

libmitfeatures.mit_profile_reset.restype = None
libmitfeatures.mit_profile_reset.argtypes = None

libmitfeatures.mit_profile_dump.argtypes = [c_int]
