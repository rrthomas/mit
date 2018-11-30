// enum type for the opcodes.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#ifndef PACKAGE_UPPER_OPCODES
#define PACKAGE_UPPER_OPCODES


enum {
    O_NOP = 0x80,
    O_POP,
    O_PUSH,
    O_SWAP,
    O_RPUSH,
    O_POP2R,
    O_RPOP,
    O_LT,
    O_EQ,
    O_ULT,
    O_ADD,
    O_MUL,
    O_UDIVMOD,
    O_DIVMOD,
    O_NEGATE,
    O_INVERT,
    O_AND,
    O_OR,
    O_XOR,
    O_LSHIFT,
    O_RSHIFT,
    O_LOAD,
    O_STORE,
    O_LOADB,
    O_STOREB,
    O_BRANCH,
    O_BRANCHZ,
    O_CALL,
    O_RET,
    O_THROW,
    O_HALT,
    O_CALL_NATIVE,
    O_EXTRA,
    O_PUSH_PSIZE,
    O_PUSH_SP,
    O_STORE_SP,
    O_PUSH_RP,
    O_STORE_RP,
    O_PUSH_PC,
    O_PUSH_S0,
    O_PUSH_SSIZE,
    O_PUSH_R0,
    O_PUSH_RSIZE,
    O_PUSH_HANDLER,
    O_STORE_HANDLER,
    O_PUSH_MEMORY,
    O_PUSH_BADPC,
    O_PUSH_INVALID,
    O_UNDEFINED, // Not part of the spec
    O_UNDEFINED_END = 0xbf
};

enum {
    OX_ARGC,
    OX_ARG,
    OX_STDIN,
    OX_STDOUT,
    OX_STDERR,
    OX_OPEN_FILE,
    OX_CLOSE_FILE,
    OX_READ_FILE,
    OX_WRITE_FILE,
    OX_FILE_POSITION,
    OX_REPOSITION_FILE,
    OX_FLUSH_FILE,
    OX_RENAME_FILE,
    OX_DELETE_FILE,
    OX_FILE_SIZE,
    OX_RESIZE_FILE,
    OX_FILE_STATUS,
};


#endif
