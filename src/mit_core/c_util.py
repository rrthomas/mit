'''
C utilities.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''


import textwrap


try:
    from .type_sizes import type_sizes

    def load_stack_type(name, type, depth):
        '''
        Generate C code to load the variable `name` of type `type` occupying
        stack slots starting at position `depth`.

        Returns a str.
        '''
        words = type_sizes[type] // type_sizes['mit_WORD']
        code = [
            'mit_max_stack_item_t temp = (mit_UWORD)(*UNCHECKED_STACK({}));'
            .format(depth)
        ]
        for i in range(words - 1):
            code.append('temp <<= mit_WORD_BIT;')
            code.append(
                'temp |= (mit_UWORD)(*UNCHECKED_STACK({}));'
                .format(depth + i + 1)
            )
        code.append(disable_warnings(['-Wint-to-pointer-cast'], '{} = ({})temp;'.format(name, type)))

        return '''\
{{
{}
}}'''.format(textwrap.indent('\n'.join(code), '    '))

    def store_stack_type(name, type, depth):
        '''
        Generate C code to store the variable `name` of type `type` occupying
        stack slots starting at position `depth`.

        Returns a str.
        '''
        words = type_sizes[type] // type_sizes['mit_WORD']
        code = [disable_warnings(['-Wpointer-to-int-cast'],
                                 'mit_max_stack_item_t temp = (mit_max_stack_item_t){};'.format(name))]
        for i in reversed(range(words - 1)):
            code.append(
                '*UNCHECKED_STACK({}) = (mit_UWORD)(temp & mit_WORD_MASK);'
                .format(depth + i + 1)
            )
            code.append('temp >>= mit_WORD_BIT;')
        code.append(
            '*UNCHECKED_STACK({}) = (mit_UWORD)({});'
            .format(depth, 'temp & mit_WORD_MASK' if words > 1 else 'temp')
        )
        return '''\
{{
{}
}}'''.format(textwrap.indent('\n'.join(code), '    '))

    def pop_stack_type(name, type):
        words = type_sizes[type] // type_sizes['mit_WORD']
        code = [
            'if (S->STACK_DEPTH < {}) RAISE(MIT_ERR_STACK_OVERFLOW);'
            .format(words),
            load_stack_type(name, type, 0),
            'S->STACK_DEPTH -= {};'.format(words),
        ]
        return '{}'.format(textwrap.indent('\n'.join(code), '    '))

    def push_stack_type(name, type):
        words = type_sizes[type] // type_sizes['mit_WORD']
        code = [
            'if (S->stack_size - S->STACK_DEPTH < {}) RAISE(MIT_ERR_STACK_WRITE);'
            .format(words),
            load_stack_type(name, type, 0),
            'S->STACK_DEPTH += {};'.format(words),
        ]
        return '{}'.format(textwrap.indent('\n'.join(code), '    '))

except:
    def load_stack_type(name, type, depth):
        return 'DUMMY CODE'
    def store_stack_type(name, type, depth):
        return 'DUMMY CODE'
    def pop_stack_type(name, type):
        return 'DUMMY CODE'
    def push_stack_type(name, type):
        return 'DUMMY CODE'

def disable_warnings(warnings, c_source):
    '''
    Returns `c_source` wrapped in "#pragmas" to suppress the given list
    `warnings` of warning flags.
    '''
    return '''\
#pragma GCC diagnostic push
{pragmas}
{c_source}
#pragma GCC diagnostic pop'''.format(c_source=c_source,
                                     pragmas='\n'.join(['#pragma GCC diagnostic ignored "{}"'.format(w)
                                                        for w in warnings]))
