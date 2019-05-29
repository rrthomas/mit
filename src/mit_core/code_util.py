'''
Code generation utilities.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import re

from mit_core.code_buffer import Code


def disable_warnings(warnings, code):
    '''
    Returns `code` wrapped in "#pragmas" to suppress the given list
    `warnings` of warning flags.

     - code - a Code.
    '''
    assert isinstance(code, Code)
    outer_code = Code()
    outer_code.append('#pragma GCC diagnostic push')
    for w in warnings:
        outer_code.append('#pragma GCC diagnostic ignored "{}"'.format(w))
    outer_code.extend(code)
    outer_code.append('#pragma GCC diagnostic pop')
    return outer_code

def c_symbol(python_symbol):
    c_symbol = re.sub('(?<!^)([A-Z])', '_\\1', python_symbol).upper()
    if not re.match('^MIT', c_symbol):
        c_symbol = 'MIT_{}'.format(c_symbol)
    return c_symbol

def enum_to_c(enum):
    '''
    Convert an Enum to C code; returns a Code.

    Values must be int.
    '''
    prefix = c_symbol(enum.__name__)
    code = Code()
    code.append('enum {')
    for member in enum:
        code.append(Code('{prefix}_{name} = {value},'.format(
            prefix=prefix,
            name=member.name,
            value=member.value
        )))
    code.append('};')
    return code

def enum_to_python(enum):
    'Convert an IntEnum to Python code; return a Code.'
    class_name = enum.__name__
    code = Code()
    code.append('''\
@unique
class {}(IntEnum):'''.format(class_name))
    for member in enum:
        code.append(Code('{name} = {value:#x}'.format(
            name=member.name,
            value=member.value,
        )))
    return code
