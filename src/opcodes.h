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
#undef INSTRUCTION
#define INSTRUCTION(name, opcode) O_ ## name = opcode,
#include "instruction-list.h"
    O_UNDEFINED, // Not part of the spec
#undef INSTRUCTION
};

enum {
    OXLIB_SMITE = -1,
    OXLIB_LIBC = 0,
};

enum {
    OX_ARGC,
    OX_ARG_LEN,
    OX_ARG_COPY,
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

enum {
    OX_SMITE_CURRENT_STATE,
    OX_SMITE_LOAD_WORD,
    OX_SMITE_STORE_WORD,
    OX_SMITE_LOAD_BYTE,
    OX_SMITE_STORE_BYTE,
    OX_SMITE_MEM_REALLOC,
    OX_SMITE_NATIVE_ADDRESS_OF_RANGE,
    OX_SMITE_RUN,
    OX_SMITE_SINGLE_STEP,
    OX_SMITE_LOAD_OBJECT,
    OX_SMITE_INIT,
    OX_SMITE_DESTROY,
    OX_SMITE_REGISTER_ARGS,
};

#endif
