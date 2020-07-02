'''
Auto-numbered Enums

Adapted from https://docs.python.org/3/library/enum.html

This file is in the public domain.
'''

from enum import Enum


class NoValue(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)


# See https://bugs.python.org/issue37062
class AutoNumber(NoValue):
    def __new__(cls, *args):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
