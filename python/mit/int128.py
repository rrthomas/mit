'''
128-bit types for Python ctypes.

(c) Mit authors 2019-2020

The package is distributed under the MIT/X11 License.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.
'''

import ctypes

from .ctypes_align import aligned_struct


class c_uint128(aligned_struct):
    _alignment_ = 16
    _fields_ = [('low', ctypes.c_uint64),
                ('high', ctypes.c_uint64)]

    def __init__(self, n=0):
        super().__init__()
        self.low = int(n) & ((1 << 64) - 1)
        self.high = int(n) >> 64

    @classmethod
    def from_param(cls, value):
        return cls(value)

    @property
    def value(self):
        return self.low | (self.high << 64)

    def __index__(self):
        return self.value

    def __int__(self):
        return self.__index__()

    def __hash__(self):
        return int.__hash__(self.value)

class c_int128(c_uint128):
    @classmethod
    def from_param(cls, value):
        return cls(value)

    @property
    def value(self):
        val = self.low | (self.high << 64)
        if val & (1 << 127) != 0: val = val | ~((1 << 128) - 1)
        return val
