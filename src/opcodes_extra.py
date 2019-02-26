# EXTRA instruction opcodes
#
# (c) Reuben Thomas 2019
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

from enum import IntEnum, unique

@unique
class LibActions(IntEnum):
    LIB_SMITE = 0x3f
    LIB_C = 0x3e

@unique
class LibcLib(IntEnum):
    ARGC = 0x0
    ARG_LEN = 0x1
    ARG_COPY = 0x2
    STDIN = 0x3
    STDOUT = 0x4
    STDERR = 0x5
    OPEN_FILE = 0x6
    CLOSE_FILE = 0x7
    READ_FILE = 0x8
    WRITE_FILE = 0x9
    FILE_POSITION = 0xa
    REPOSITION_FILE = 0xb
    FLUSH_FILE = 0xc
    RENAME_FILE = 0xd
    DELETE_FILE = 0xe
    FILE_SIZE = 0xf
    RESIZE_FILE = 0x10
    FILE_STATUS = 0x11

@unique
class SMiteLib(IntEnum):
    CURRENT_STATE = 0x0
    LOAD_WORD = 0x1
    STORE_WORD = 0x2
    LOAD_BYTE = 0x3
    STORE_BYTE = 0x4
    REALLOC_MEMORY = 0x5
    REALLOC_STACK = 0x6
    NATIVE_ADDRESS_OF_RANGE = 0x7
    RUN = 0x8
    SINGLE_STEP = 0x9
    LOAD_OBJECT = 0xa
    INIT = 0xb
    DESTROY = 0xc
    REGISTER_ARGS = 0xd
