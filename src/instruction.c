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


#define _ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)                  \
    {                                                                   \
        size_t len = 0;                                                 \
        smite_BYTE b;                                                   \
        int error;                                                      \
                                                                        \
        /* Continuation bytes */                                        \
        for (int bits = smite_find_msbit(v) + 1; bits > INSTRUCTION_CHUNK_BIT; bits -= INSTRUCTION_CHUNK_BIT) { \
            b = (smite_BYTE)(v & INSTRUCTION_CHUNK_MASK) | INSTRUCTION_CONTINUATION_BIT; \
            if ((error = STORE(b)) != 0)                                \
                return (ptrdiff_t)error;                                \
            len++;                                                      \
            v = ARSHIFT(v, INSTRUCTION_CHUNK_BIT);                      \
        }                                                               \
                                                                        \
        /* Set number bit if needed */                                  \
        if (type == INSTRUCTION_NUMBER)                                 \
            v |= INSTRUCTION_NUMBER_BIT;                                \
                                                                        \
        /* Last (or only) byte */                                       \
        b = (smite_BYTE)v;                                              \
        if ((error = STORE(b)))                                         \
            return (ptrdiff_t)error;                                    \
        len++;                                                          \
                                                                        \
        return len;                                                     \
    }

#define STATEFUL_ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)          \
    ptrdiff_t NAME(smite_state *S, TYPE HANDLE, enum instruction_type type, smite_WORD v) \
    _ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)

#define STORE_VIRTUAL(b) (smite_store_byte(S, addr++, (b)))
STATEFUL_ENCODE_INSTRUCTION(smite_encode_instruction, smite_UWORD, addr, STORE_VIRTUAL)

#define _DECODE_INSTRUCTION(RET_TYPE, NAME, TYPE, HANDLE, LOAD)         \
    {                                                                   \
        unsigned bits = 0;                                              \
        smite_WORD n = 0;                                               \
        smite_BYTE b;                                                   \
        RET_TYPE error;                                                 \
        int type = INSTRUCTION_ACTION;                                  \
                                                                        \
        /* Continuation bytes */                                        \
        for (error = LOAD(b);                                           \
             error >= 0 && bits <= smite_word_bit - INSTRUCTION_CHUNK_BIT && \
                 (b & ~INSTRUCTION_CHUNK_MASK) == INSTRUCTION_CONTINUATION_BIT; \
             error = LOAD(b)) {                                         \
            n |= (smite_WORD)(b & INSTRUCTION_CHUNK_MASK) << bits;      \
            bits += INSTRUCTION_CHUNK_BIT;                              \
        }                                                               \
        if (bits > smite_word_bit)                                      \
            return -2;                                                  \
        if (error < 0)                                                  \
            return error;                                               \
                                                                        \
        /* Check for number opcode */                                   \
        if ((b & INSTRUCTION_NUMBER_BIT) == INSTRUCTION_NUMBER_BIT) {   \
            type = INSTRUCTION_NUMBER;                                  \
            if (smite_word_bit - bits < smite_byte_bit)                 \
                b &= (1 << (smite_word_bit - bits)) - 1;                \
        }                                                               \
                                                                        \
        /* Final (or only) byte */                                      \
        n |= (smite_UWORD)b << bits;                                    \
        bits += smite_byte_bit - 1;                                     \
        if (type == INSTRUCTION_NUMBER && bits < smite_word_bit)        \
            n = ARSHIFT((smite_UWORD)n << (smite_word_bit - bits), smite_word_bit - bits); \
        *val = n;                                                       \
        return type;                                                    \
    }

#define STATEFUL_DECODE_INSTRUCTION(RET_TYPE, NAME, TYPE, HANDLE, LOAD) \
    RET_TYPE NAME(smite_state *S, TYPE HANDLE, smite_WORD *val)         \
    _DECODE_INSTRUCTION(RET_TYPE, NAME, TYPE, HANDLE, LOAD)

#define LOAD_VIRTUAL(b) (smite_load_byte(S, (*addr)++, &(b)))
STATEFUL_DECODE_INSTRUCTION(int, smite_decode_instruction, smite_UWORD *, addr, LOAD_VIRTUAL)
