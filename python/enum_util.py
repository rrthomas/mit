# Enum code generation utilities
#
# (c) Mit authors 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

def print_enum(enum, class_name, prefix):
    '''Print an IntEnum as a Python Enum.'''
    print('''\
@unique
class {}(IntEnum):'''.format(class_name))
    for member in enum:
        print('    {}{} = {:#x}'.format(
            prefix,
            member.name,
            member.value,
        ))
    print('')
