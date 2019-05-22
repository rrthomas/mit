'''
Collect generated code, and indent it correctly.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import textwrap


class Code:
    '''
    Represents a list of code fragments, each of which is a str or a Code.
    The latter will be indented on output.
    '''
    def __init__(self, *args):
        self.buffer = []
        for arg in args:
            self.append(arg)

    INDENT = '    '

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

    def __repr__(self):
        return 'Code(\n{}\n)'.format(textwrap.indent(
            ',\n'.join(repr(x) for x in self.buffer),
            self.INDENT,
        ))

    def __str__(self):
        return textwrap.indent(
            '\n'.join(str(x) for x in self.buffer),
            self.INDENT,
        )
