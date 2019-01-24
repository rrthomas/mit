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

#include "external-syms.h"

#include <unistd.h>

#include "public.h"
#include "aux.h"
#include "opcodes.h"


#define _ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)                  \
    {                                                                   \
        size_t len = 0;                                                 \
        BYTE b;                                                         \
        int exception;                                                  \
                                                                        \
        /* Continuation bytes */                                        \
        for (int bits = find_msbit(v) + 1; bits > INSTRUCTION_CHUNK_BIT; bits -= INSTRUCTION_CHUNK_BIT) { \
            b = (BYTE)(v & INSTRUCTION_CHUNK_MASK) | 0x40;              \
            if ((exception = STORE(b)) != 0)                            \
                return (ptrdiff_t)exception;                            \
            len++;                                                      \
            v = ARSHIFT(v, INSTRUCTION_CHUNK_BIT);                      \
        }                                                               \
                                                                        \
        /* Set action bit if needed */                                  \
        if (type == INSTRUCTION_ACTION)                                 \
            v |= 0x80;                                                  \
                                                                        \
        /* Last (or only) byte */                                       \
        b = (BYTE)v;                                                    \
        if ((exception = STORE(b)))                                     \
            return (ptrdiff_t)exception;                                \
        len++;                                                          \
                                                                        \
        return len;                                                     \
    }

#define ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)                   \
    ptrdiff_t NAME(TYPE HANDLE, enum instruction_type type, WORD v)     \
    _ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)

#define STATEFUL_ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)          \
    ptrdiff_t NAME(state *S, TYPE HANDLE, enum instruction_type type, WORD v) \
    _ENCODE_INSTRUCTION(NAME, TYPE, HANDLE, STORE)

#define STORE_FILE(b) (-(write(fd, &b, 1) != 1))
ENCODE_INSTRUCTION(encode_instruction_file, int, fd, STORE_FILE)

#define STORE_VIRTUAL(b) (store_byte(S, addr++, (b)))
STATEFUL_ENCODE_INSTRUCTION(encode_instruction, UWORD, addr, STORE_VIRTUAL)

#define _DECODE_INSTRUCTION(NAME, TYPE, HANDLE, LOAD)                   \
    {                                                                   \
        unsigned bits = 0;                                              \
        WORD n = 0;                                                     \
        BYTE b;                                                         \
        int exception;                                                  \
        int type = INSTRUCTION_NUMBER;                                  \
                                                                        \
        /* Continuation bytes */                                        \
        for (exception = LOAD(b); exception == 0 && (b & ~INSTRUCTION_CHUNK_MASK) == 0x40; exception = LOAD(b)) { \
            n |= (WORD)(b & INSTRUCTION_CHUNK_MASK) << bits;            \
            bits += INSTRUCTION_CHUNK_BIT;                              \
        }                                                               \
        if (exception != 0)                                             \
            return exception;                                           \
                                                                        \
        /* Check for action opcode */                                   \
        /* FIXME: Test for instruction should be macro */               \
        if ((b & ~INSTRUCTION_CHUNK_MASK) == 0x80) {                    \
            type = INSTRUCTION_ACTION;                                  \
            b &= INSTRUCTION_CHUNK_MASK;                                \
        }  else if (word_bit - bits < byte_bit)                         \
            b &= (1 << (word_bit - bits)) - 1;                          \
                                                                        \
        /* Final (or only) byte */                                      \
        n |= (UWORD)b << bits;                                          \
        bits += byte_bit;                                               \
        if (type == INSTRUCTION_NUMBER && bits < word_bit)              \
            n = ARSHIFT((UWORD)n << (word_bit - bits), word_bit - bits); \
        *val = n;                                                       \
        return type;                                                    \
    }

#define DECODE_INSTRUCTION(NAME, TYPE, HANDLE, LOAD)                    \
    int NAME(TYPE HANDLE, WORD *val)                                    \
    _DECODE_INSTRUCTION(NAME, TYPE, HANDLE, LOAD)

#define STATEFUL_DECODE_INSTRUCTION(NAME, TYPE, HANDLE, LOAD)           \
    int NAME(state *S, TYPE HANDLE, WORD *val)                          \
    _DECODE_INSTRUCTION(NAME, TYPE, HANDLE, LOAD)

#define LOAD_FILE(b) (-(read(fd, &b, 1) != 1))
DECODE_INSTRUCTION(decode_instruction_file, int, fd, LOAD_FILE)

#define LOAD_VIRTUAL(b) (load_byte(S, (*addr)++, &(b)))
STATEFUL_DECODE_INSTRUCTION(decode_instruction, UWORD *, addr, LOAD_VIRTUAL)
