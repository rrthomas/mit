// Instruction opcodes.
//
// (c) Reuben Thomas 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef SMITE_OPCODES
#define SMITE_OPCODES


#define INSTRUCTION(name, opcode) name = opcode,
#include "opcodes-core.h"
#undef INSTRUCTION

#define INSTRUCTION(name, opcode) name = opcode,
#include "opcodes-extra.h"
#undef INSTRUCTION


#endif
