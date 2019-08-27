'''
Class for registers.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

from .autonumber import AutoNumber


class RegisterEnum(AutoNumber):
    def __init__(self, read_only=False, type='mit_uword'):
        self.read_only = read_only
        self.type = type
