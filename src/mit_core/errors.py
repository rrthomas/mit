# API errors
#
# (c) Mit authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import IntEnum, unique

@unique
class MallocError(IntEnum):
    OK = 0
    CANNOT_ALLOCATE_MEMORY = -1

@unique
class LoadError(IntEnum):
    UNALIGNED_ADDRESS = -1
    INVALID_ADDRESS_RANGE = -2
    FILE_SYSTEM_ERROR = -3
    INVALID_OBJECT_FILE = -4
    INCOMPATIBLE_OBJECT_FILE = -5
    OBJECT_FILE_TOO_LARGE = -6

@unique
class SaveError(IntEnum):
    OK = 0
    UNALIGNED_ADDRESS = -1
    INVALID_ADDRESS_RANGE = -2
    FILE_SYSTEM_ERROR = -3
