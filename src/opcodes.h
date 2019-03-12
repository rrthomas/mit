// Instruction opcodes.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef SMITE_OPCODES
#define SMITE_OPCODES


// Instruction encoding
enum {
#define TYPE(name, opcode) INSTRUCTION_ ## name = opcode,
#include "instruction-type-list.h"
#undef TYPE
};

enum {
#define INSTRUCTION(name, opcode) O_ ## name = opcode,
#include "instruction-list.h"
    O_UNDEFINED, // Not part of the spec
#undef INSTRUCTION
};

#define INSTRUCTION(name, opcode) name = opcode,
#include "opcodes-extra.h"


#endif
