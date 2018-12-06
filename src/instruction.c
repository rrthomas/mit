// Encode and decode instructions.
//
// (c) Reuben Thomas 2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "external_syms.h"

#include "public.h"
#include "aux.h"
#include "opcodes.h"


int encode_instruction(UWORD *addr, enum instruction_type type, WORD v)
{
    int exception;
    // Continuation bytes
    for (unsigned bits = find_msbit(v) + 1; bits > INSTRUCTION_CHUNK_BIT; bits -= INSTRUCTION_CHUNK_BIT) {
        if ((exception = store_byte((*addr)++, (BYTE)(v & INSTRUCTION_CHUNK_MASK) | 0x40)) != 0)
            return exception;
        v = ARSHIFT(v, INSTRUCTION_CHUNK_BIT);
    }

    // Set action bit if needed
    if (type == INSTRUCTION_ACTION)
        v |= 0x80;

    // Last (or only) byte
    return store_byte((*addr)++, (BYTE)v);
}

int decode_instruction(UWORD *addr, WORD *val)
{
    unsigned bits = 0;
    WORD n = 0;
    BYTE b;
    int exception;
    int type = INSTRUCTION_NUMBER;

    // Continuation bytes
    for (exception = load_byte((*addr)++, &b); exception == 0 && (b & ~INSTRUCTION_CHUNK_MASK) == 0x40; exception = load_byte((*addr)++, &b)) {
        n |= (b & INSTRUCTION_CHUNK_MASK) << bits;
        bits += INSTRUCTION_CHUNK_BIT;
    }
    if (exception != 0)
        return exception;

    // Check for action opcode
    if ((b & ~INSTRUCTION_CHUNK_MASK) == 0x80) {
        type = INSTRUCTION_ACTION;
        b &= INSTRUCTION_CHUNK_MASK;
    }

    // Final (or only) byte
    n |= b << bits;
    bits += BYTE_BIT;
    if (type == INSTRUCTION_NUMBER && bits < WORD_BIT)
        n = ARSHIFT(n << (WORD_BIT - bits), WORD_BIT - bits);
    *val = n;
    return type;
}
