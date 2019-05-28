'''
Code generation utilities.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

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
