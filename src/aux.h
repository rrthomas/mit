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


// Stacks location and size
#define DATA_STACK_SEGMENT   0xfe000000
#define RETURN_STACK_SEGMENT 0xff000000
#define DEFAULT_STACK_SIZE   16384
#define MAX_STACK_SIZE       67108864

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
    (SP += WORD_W * STACK_DIRECTION, STORE_WORD(SP, (v)))
#define POP                                     \
    (SP -= WORD_W * STACK_DIRECTION, LOAD_WORD(SP + WORD_W * STACK_DIRECTION))
#define PUSH_DOUBLE(ud)                         \
    PUSH((UWORD)(ud & WORD_MASK));              \
    PUSH((UWORD)((ud >> WORD_BIT) & WORD_MASK))
#define POP_DOUBLE                              \
    (SP -= 2 * WORD_W * STACK_DIRECTION, (UWORD)LOAD_WORD(SP + WORD_W * STACK_DIRECTION), temp | \
     ((DUWORD)(UWORD)_LOAD_WORD(SP + 2 * WORD_W * STACK_DIRECTION, temp2) << WORD_BIT))
#define PUSH_RETURN(v)                          \
    (RP += WORD_W * STACK_DIRECTION, STORE_WORD(RP, (v)))
#define POP_RETURN                              \
    (RP -= WORD_W * STACK_DIRECTION, LOAD_WORD(RP + WORD_W * STACK_DIRECTION))
#define STACK_UNDERFLOW(ptr, base)              \
    (ptr - base == 0 ? false : (STACK_DIRECTION > 0 ? ptr < base : ptr > base))

uint8_t *native_address_range_in_one_area(UWORD start, UWORD length, bool writable);

// Align a VM address
#define ALIGN(a) ((a + WORD_W - 1) & (-WORD_W))

// Check whether a VM address is aligned
#define IS_ALIGNED(a)     (((a) & (WORD_W - 1)) == 0)

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#define ARSHIFT(n, p) (((n) >> (p)) | (-((n) < 0) << (WORD_BIT - p)))

#define LOAD_I (exception = (load_byte(PC++, &I)))

// Literals
#define LITERAL_CHUNK_BIT 6
#define LITERAL_CHUNK_MASK ((1 << LITERAL_CHUNK_BIT) - 1)


#endif
