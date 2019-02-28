// Encode and decode instructions.
//
// (c) Reuben Thomas 2018-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stddef.h>
#include <unistd.h>

#include "smite.h"
#include "aux.h"
#include "opcodes.h"


ptrdiff_t smite_encode_instruction(
    smite_state *S,
    smite_UWORD addr,
    enum instruction_type type,
    smite_WORD v)
{
    smite_UWORD start_addr = addr;
    smite_BYTE b;
    int error;

    // Continuation bytes.
    for (int bits = smite_find_msbit(v) + 1;
        bits > INSTRUCTION_CHUNK_BITS;
        bits -= INSTRUCTION_CHUNK_BITS)
    {
        b = (smite_BYTE)(v & INSTRUCTION_CHUNK_MASK) |
            INSTRUCTION_CONTINUATION_BIT;
        if ((error = smite_store_byte(S, addr++, b)) != 0)
            return (ptrdiff_t)error;
        v = ARSHIFT(v, INSTRUCTION_CHUNK_BITS);
    }

    // Set number bit if needed.
    if (type == INSTRUCTION_NUMBER)
        v |= INSTRUCTION_NUMBER_BIT;

    // Last (or only) byte.
    b = (smite_BYTE)v;
    if ((error = smite_store_byte(S, addr++, b)) != 0)
        return (ptrdiff_t)error;
    return addr - start_addr;
}

int smite_decode_instruction(
    smite_state *S,
    smite_UWORD *addr,
    smite_WORD *val)
{
    int error;
    unsigned bits = 0;
    smite_WORD n = 0;
    smite_BYTE b;

    // First byte.
    if ((error = smite_load_byte(S, (*addr)++, &b)) != 0)
        return error;
        
    // Check for action opcode.
    if ((b & ~INSTRUCTION_CHUNK_MASK) == 0) {
        *val = (smite_UWORD)b;
        return INSTRUCTION_ACTION;
    }

    // Continuation bytes.
    for (bits = 0;
        (b & ~INSTRUCTION_CHUNK_MASK) == INSTRUCTION_CONTINUATION_BIT;
        bits += INSTRUCTION_CHUNK_BITS)
    {
        n |= (smite_WORD)(b & INSTRUCTION_CHUNK_MASK) << bits;
        if ((error = smite_load_byte(S, (*addr)++, &b)) != 0)
            return error;
    }

    // Final (or only) byte must be sign extended.
    if (bits >= smite_word_bit || (b & INSTRUCTION_NUMBER_BIT) == 0)
        return -2;
    const unsigned shift_distance =
        smite_word_bit - (INSTRUCTION_CHUNK_BITS + 1);
    smite_WORD w = ARSHIFT((smite_UWORD)b << shift_distance, shift_distance);
    *val = n | (w << bits);

    return INSTRUCTION_NUMBER;
}

