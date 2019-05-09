'''
C utilities.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''


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
