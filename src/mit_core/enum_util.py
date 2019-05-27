# Utilities for converting Enums to code for output.
#
# (c) Mit authors 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from .code_buffer import Code


def enum_to_c(enum, prefix):
    '''
    Convert an Enum to C code; returns a Code.

    Values must be int.
    '''
    code = Code()
    code.append('enum {')
    for member in enum:
        code.append(Code('{}{} = {},'.format(prefix, member.name, member.value)))
    code.append('};')
    return code

def enum_to_python(enum, class_name, prefix):
    'Convert an IntEnum to Python code; return a Code.'
    code = Code()
    code.append('''\
@unique
class {}(IntEnum):'''.format(class_name))
    for member in enum:
        code.append(Code('{}{} = {:#x}'.format(
            prefix,
            member.name,
            member.value,
        )))
    return code
