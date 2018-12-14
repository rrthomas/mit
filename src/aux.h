// Auxiliary public functions.
// These are undocumented and subject to change.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#ifndef PACKAGE_UPPER_AUX
#define PACKAGE_UPPER_AUX


#include "config.h"

#include <stdio.h>      // for the FILE type
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>

#include "opcodes.h"


// Stacks location and size
#define DATA_STACK_SEGMENT   0xfe000000
#define RETURN_STACK_SEGMENT 0xff000000
#define DEFAULT_STACK_SIZE   16384
#define MAX_STACK_SIZE       67108864

// Initialisation helper
#define init_alloc(n) (init((WORD *)calloc((n), WORD_SIZE), (n)))

// Memory access

// Return value is 0 if OK, or exception code for invalid or unaligned address
WORD reverse_word(WORD value);
int reverse(UWORD start, UWORD length);

#define STACK_DIRECTION 1
#define _LOAD_WORD(a, temp)                                             \
    ((exception = exception ? exception : load_word((a), &temp)), temp)
#define LOAD_WORD(a) _LOAD_WORD(a, temp)
#define STORE_WORD(a, v)                                                \
    (exception = exception ? exception : store_word((a), (v)))
#define LOAD_BYTE(a)                                                    \
    ((exception = exception ? exception : load_byte((a), &byte)), byte)
#define STORE_BYTE(a, v)                                                \
    (exception = exception ? exception : store_byte((a), (v)))
#define PUSH(v)                                 \
    (SP += WORD_SIZE * STACK_DIRECTION, STORE_WORD(SP, (v)))
#define POP                                     \
    (SP -= WORD_SIZE * STACK_DIRECTION, LOAD_WORD(SP + WORD_SIZE * STACK_DIRECTION))
#if WORD_SIZE == 4
#define PUSH64(ud)                              \
    PUSH((UWORD)(ud & WORD_MASK));              \
    PUSH((UWORD)((ud >> WORD_BIT) & WORD_MASK))
#define POP64                                   \
    (SP -= 2 * WORD_SIZE * STACK_DIRECTION, (UWORD)LOAD_WORD(SP + WORD_SIZE * STACK_DIRECTION), temp | \
     ((uint64_t)(UWORD)_LOAD_WORD(SP + 2 * WORD_SIZE * STACK_DIRECTION, temp2) << WORD_BIT))
#elif WORD_SIZE == 8
#define PUSH64 PUSH
#define POP64  POP
#else
#error "WORD_SIZE is not 4 or 8!"
#endif
#define PUSH_RETURN(v)                          \
    (RP += WORD_SIZE * STACK_DIRECTION, STORE_WORD(RP, (v)))
#define POP_RETURN                              \
    (RP -= WORD_SIZE * STACK_DIRECTION, LOAD_WORD(RP + WORD_SIZE * STACK_DIRECTION))
#define STACK_UNDERFLOW(ptr, base)              \
    (ptr - base == 0 ? false : (STACK_DIRECTION > 0 ? ptr < base : ptr > base))

uint8_t *native_address_range_in_one_area(UWORD start, UWORD length, bool writable);

// Align a VM address
#define ALIGN(a) ((a + WORD_SIZE - 1) & (-WORD_SIZE))

// Check whether a VM address is aligned
#define IS_ALIGNED(a)     (((a) & (WORD_SIZE - 1)) == 0)

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#define ARSHIFT(n, p) (((n) >> (p)) | ((typeof(n))(-((n) < 0)) << (WORD_BIT - (p))))

ptrdiff_t encode_instruction_native(BYTE *addr, enum instruction_type type, WORD v);
ptrdiff_t encode_instruction(UWORD *addr, enum instruction_type type, WORD v);
int decode_instruction_file(FILE *file, WORD *val);
int decode_instruction(UWORD *addr, WORD *val);

// Bit utilities

_GL_ATTRIBUTE_CONST int find_msbit(WORD v); // return msbit of a WORD
int byte_size(WORD v); // return number of significant bytes in a WORD quantity

// Instructions
#define INSTRUCTION_CHUNK_BIT 6
#define INSTRUCTION_CHUNK_MASK ((1 << INSTRUCTION_CHUNK_BIT) - 1)
#define INSTRUCTION_MAX_CHUNKS (((WORD_BIT + INSTRUCTION_CHUNK_BIT - 1) / INSTRUCTION_CHUNK_BIT))

// Object files
#define MAGIC_LENGTH 8


#endif
