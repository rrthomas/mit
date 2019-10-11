# Features API errors
#
# (c) Mit authors 2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import IntEnum, unique

@unique
class RegisterArgsErrorCode(IntEnum):
    'Error codes returned by `mit_register_args`.'
    TOO_FEW_ARGUMENTS = -1
