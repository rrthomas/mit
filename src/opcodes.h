// enum type for the opcodes to make the interpreter more readable. Opcode
// names which are not valid C identifiers have been altered.
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
    O_NEXT00,
    O_DROP,
    O_DUP,
    O_SWAP,
    O_RDUP,
    O_TOR,
    O_RFROM,
    O_LESS,
    O_EQUAL,
    O_ULESS,
    O_PLUS,
    O_STAR,
    O_UMODSLASH,
    O_SREMSLASH,
    O_NEGATE,
    O_INVERT,
    O_AND,
    O_OR,
    O_XOR,
    O_LSHIFT,
    O_RSHIFT,
    O_FETCH,
    O_STORE,
    O_CFETCH,
    O_CSTORE,
    O_SPFETCH,
    O_SPSTORE,
    O_RPFETCH,
    O_RPSTORE,
    O_EPFETCH,
    O_EPSTORE,
    O_QEPSTORE,
    O_S0FETCH,
    O_HASHS,
    O_R0FETCH,
    O_HASHR,
    O_THROWFETCH,
    O_THROWSTORE,
    O_MEMORYFETCH,
    O_BADFETCH,
    O_NOT_ADDRESSFETCH,
    O_EXECUTE,
    O_EXIT,
    O_THROW,
    O_HALT,
    O_LINK,
    O_LITERAL,
    O_UNDEFINED = 0x7f, // Not part of the spec, just an arbitrary undefined opcode
    OX_ARGC = 0x80,
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
    O_NEXTFF = 0xff
};


#endif
