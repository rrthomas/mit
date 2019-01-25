// Instruction opcodes.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#ifndef SMITE_OPCODES
#define SMITE_OPCODES


// Instruction encoding
enum instruction_type {
#define TYPE(name, opcode) INSTRUCTION_ ## name = opcode,
#include "instruction-type-list.h"
#undef TYPE
};

enum {
#undef INSTRUCTION
#define INSTRUCTION(name, opcode) O_ ## name = opcode,
#include "instruction-list.h"
    O_UNDEFINED, // Not part of the spec
#undef INSTRUCTION
};

#include "opcodes-extra.h"


#endif
