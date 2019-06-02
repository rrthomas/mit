'''
Code generation utilities.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import re
import textwrap

from .params import *


class Code:
    '''
    Collect generated code, and indent it correctly.
    Represents a list of code fragments, each of which is a str or a Code.
    The latter will be indented on output.
    '''
    def __init__(self, *args):
        self.buffer = []
        for arg in args:
            self.append(arg)

    INDENT = '    '

    def __repr__(self):
        '''
        Returns a valid Python expression.
        '''
        return 'Code(\n{}\n)'.format(textwrap.indent(
            ',\n'.join(repr(x) for x in self.buffer),
            self.INDENT,
        ))

    def __str__(self):
        '''
        Returns this Code as a str.
        '''
        return '\n'.join(
            textwrap.indent(str(x), self.INDENT)
            if isinstance(x, Code) else str(x)
            for x in self.buffer
        )

    def append(self, str_or_code):
        assert isinstance(str_or_code, (Code, str))
        if isinstance(str_or_code, str):
            str_or_code = textwrap.dedent(str_or_code.rstrip())
        self.buffer.append(str_or_code)

    def extend(self, code):
        assert isinstance(code, Code)
        self.buffer.extend(code.buffer)

    def format(self, *args, **kwargs):
        return Code(*(x.format(*args, **kwargs) for x in self.buffer))


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


# Various helper routines for instruction action code

def RAISE(error_code):
    return Code(*['''\
        {{
            error = ({});
            goto error;
        }}'''.format(error_code)
    ])

def CHECK_ALIGNED(addr):
    return Code(*['''\
        if (!is_aligned(({addr}), MIT_SIZE_WORD)) {{
            S->BAD = ({addr});'''.format(addr=addr),
            RAISE('MIT_ERROR_UNALIGNED_ADDRESS'),
        '}',
    ])

def CHECK_ADDRESS(addr):
    return Code(*['''\
        if (unlikely(({addr}) >= S->memory_size - MIT_WORD_BYTES)) {{
            S->BAD = ({addr});'''.format(addr=addr),
            RAISE('MIT_ERROR_INVALID_MEMORY_READ'),
        '}'
    ])

def LOAD_WORD(w, addr):
    if endism == host_endism:
        return Code(*[
            '{',
                CHECK_ADDRESS(addr), '''\
                #pragma GCC diagnostic push
                #pragma GCC diagnostic ignored "-Wcast-align"
                    ({w}) = *(mit_word *)((uint8_t *)S->memory + ({addr}));
                #pragma GCC diagnostic pop'''
                .format(w=w, addr=addr),
            '}',
        ])
    else:
        return Code(*[
            '{',
                CHECK_ADDRESS(addr), '''\
                mit_word p = 0;
                load(S->memory, S->memory_size, ({addr}), MIT_SIZE_WORD, &p);
                ({w}) = p;'''.format(w=w, addr=addr),
            '}',
        ])

FETCH = Code(*['''\
    {
        initial_PC = S->PC;
        initial_I = S->I;
        S->I >>= MIT_OPCODE_BIT;
    }'''
])

DO_NEXT = Code(*[
    '{',
        LOAD_WORD('S->I', 'S->PC'),
        'S->PC += MIT_WORD_BYTES;',
    '}',
])
