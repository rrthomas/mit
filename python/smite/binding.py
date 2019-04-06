'''
Python bindings for libsmite.

(c) SMite authors 2019

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from ctypes import *
from ctypes.util import find_library

library_file = find_library("smite")
if not library_file:
    # For Windows
    # FIXME: Do this portably
    # FIXME: Substitute version when library is versioned
    library_file = find_library("libsmite-0")
assert(library_file)
libsmite = CDLL(library_file)
assert(libsmite)

# Errors
class Error(Exception):
    pass

class ErrorCode(Error):
    def __init__(self, error_code, message):
        super().__init__(error_code, message)

def errcheck(code_to_message):
    '''
    Returns a callback suitable for use as `ctypes._FuncPtr.errcheck`.
     - code_to_message - a dict from int to message. If the message is `None`
       the code is considered to be a success, and `None` is returned.
       If the code is not found in `code_to_message`:
        - if a `None` code exists, an "unknown error" is reported.
        - otherwise the result is returned unchanged.
    '''
    require_match = None in code_to_message.values()
    def callback(result, _func, _args):
        if result in code_to_message:
            message = code_to_message[result]
            if message is None:
                return
        elif require_match:
            message = "unknown error!"
        else:
            return result
        raise ErrorCode(result, message)
    return callback


# Constants (all of type unsigned)
vars().update([(c, c_uint.in_dll(libsmite, "smite_{}".format(c)).value)
               for c in ["word_size", "size_word",
                         "byte_bit", "byte_mask", "word_bit",
                         "instruction_bit", "instruction_mask"]])
sign_bit = 1 << (word_bit - 1)


# Types
if word_size == sizeof(c_int):
    c_word = c_int
    c_uword = c_uint
elif word_size == sizeof(c_long):
    c_word = c_long
    c_uword = c_ulong
elif word_size == sizeof(c_longlong):
    c_word = c_longlong
    c_uword = c_ulonglong
else:
    raise Exception("Could not find Python C type matching WORD (size {})".format(word_size))


# Constants that require VM types
vars().update([(c, cty.in_dll(libsmite, "smite_{}".format(c)).value)
               for (c, cty) in [
                       ("word_mask", c_uword),
                       ("uword_max", c_uword),
                       ("word_min", c_word),
                       ("word_max", c_word),
               ]])

# Functions
c_ptrdiff_t = c_ssize_t

# FIXME: Generate these from C
execution_error = errcheck({
    0: None,
    1: "invalid opcode",
    2: "bad stack depth",
    3: "invalid stack read",
    4: "invalid stack write",
    5: "invalid memory read",
    6: "invalud memory write",
    7: "unaligned address",
    8: "bad size",
    9: "division by zero",
    128: "halt",
})

malloc_error = errcheck({
    0: None,
    1: "memory allocation error",
})

# smite.h
libsmite.smite_load.argtypes = [c_void_p, c_uword, c_uint, POINTER(c_word)]
libsmite.smite_load.errcheck = execution_error
libsmite.smite_store.argtypes = [c_void_p, c_uword, c_uint, c_word]
libsmite.smite_store.errcheck = execution_error

libsmite.smite_load_stack.argtypes = [c_void_p, c_uword, POINTER(c_word)]
libsmite.smite_load_stack.errcheck = execution_error
libsmite.smite_store_stack.argtypes = [c_void_p, c_uword, c_word]
libsmite.smite_store_stack.errcheck = execution_error
libsmite.smite_pop_stack.argtypes = [c_void_p, POINTER(c_word)]
libsmite.smite_pop_stack.errcheck = execution_error
libsmite.smite_push_stack.argtypes = [c_void_p, c_word]
libsmite.smite_push_stack.errcheck = execution_error

libsmite.smite_native_address_of_range.restype = POINTER(c_ubyte)
libsmite.smite_native_address_of_range.argtypes = [c_void_p, c_uword, c_uword]

libsmite.smite_run.restype = c_word
libsmite.smite_run.argtypes = [c_void_p]
libsmite.smite_run.errcheck = execution_error

libsmite.smite_single_step.restype = c_word
libsmite.smite_single_step.argtypes = [c_void_p]
libsmite.smite_single_step.errcheck = execution_error

libsmite.smite_load_object.restype = c_ptrdiff_t
libsmite.smite_load_object.argtypes = [c_void_p, c_uword, c_int]
libsmite.smite_load_object.errcheck = errcheck({
    -1: "file system error",
    -2: "module invalid",
    -3: "module has wrong ENDISM or WORD_SIZE",
    -4: "address out of range or unaligned, or module too large",
})

libsmite.smite_save_object.argtypes = [c_void_p, c_uword, c_uword, c_int]
libsmite.smite_save_object.errcheck = errcheck({
    0: None,
    -1: "file system error",
    -2: "address out of range or unaligned",
})

libsmite.smite_init.restype = c_void_p
libsmite.smite_init.argtypes = [c_size_t, c_size_t]

libsmite.smite_realloc_memory.argtypes = [c_void_p, c_int]
libsmite.smite_realloc_memory.errcheck = malloc_error

libsmite.smite_realloc_stack.argtypes = [c_void_p, c_int]
libsmite.smite_realloc_stack.errcheck = malloc_error

libsmite.smite_destroy.restype = None
libsmite.smite_destroy.argtypes = [c_void_p]

libsmite.smite_register_args.argtypes = [c_void_p, c_int, c_void_p]

libsmite.smite_align.restype = c_uword
libsmite.smite_align.argtypes = [c_uword]

libsmite.smite_is_aligned.argtypes = [c_uword]

def align(addr):
    return libsmite.smite_align(addr, size_word)

def is_aligned(addr):
    return libsmite.smite_is_aligned(addr, size_word)
