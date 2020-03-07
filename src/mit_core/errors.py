# API errors
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import IntEnum, unique

@unique
class LoadErrorCode(IntEnum):
    'Error codes returned by `mit_load_object()`.'
    UNALIGNED_ADDRESS = -1
    INVALID_ADDRESS_RANGE = -2
    FILE_SYSTEM_ERROR = -3
    INVALID_OBJECT_FILE = -4
    INCOMPATIBLE_OBJECT_FILE = -5

@unique
class SaveErrorCode(IntEnum):
    'Error codes returned by `mit_save_object()`.'
    UNALIGNED_ADDRESS = -1
    INVALID_ADDRESS_RANGE = -2
    FILE_SYSTEM_ERROR = -3
