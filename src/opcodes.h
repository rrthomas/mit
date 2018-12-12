// Instruction opcodes.
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


// Instruction encoding
enum instruction_type {
      INSTRUCTION_NUMBER,
      INSTRUCTION_ACTION,
};

enum {
#include "instruction-names.h"
    O_UNDEFINED, // Not part of the spec
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
