'''
Class for registers.

Copyright (c) 2019 Mit authors

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import re
from enum import Enum


# Copied from https://docs.python.org/3/library/enum.html
class NoValue(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

# Adapted from https://docs.python.org/3/library/enum.html
# See https://bugs.python.org/issue37062
class AutoNumber(NoValue):
    def __new__(cls, *args):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

class AbstractRegister(AutoNumber):
    def __init__(self, type=None):
        self.type = type or 'mit_uword'
        self.return_type = re.sub('restrict', '', self.type)
