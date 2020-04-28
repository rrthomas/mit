# Features API errors
#
# (c) Mit authors 2019-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import IntEnum, unique

@unique
class TrapErrorCode(IntEnum):
    'Error codes returned by `mit_trap`.'
    INVALID_LIBRARY = 16
    INVALID_FUNCTION = 17
