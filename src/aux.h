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


#include <stdio.h>      // for the FILE type
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>

#include "opcodes.h"


// Memory size
#define DEFAULT_MEMORY ((UWORD)0x100000U) // Default size of VM memory in words
#define MAX_MEMORY (((UWORD)1 << (WORD_BIT - 1)) / WORD_SIZE) // Maximum size of memory in words (half the address space)

// Stacks location and size
#define MAX_STACK_SIZE       ((((UWORD)1) << (WORD_BIT - 4)) / WORD_SIZE)
#define DATA_STACK_SEGMENT   (((UWORD)0xfeU) << (WORD_BIT - 8))
#define RETURN_STACK_SEGMENT (((UWORD)0xffU) << (WORD_BIT - 8))
#define DEFAULT_STACK_SIZE   ((UWORD)16384U)

// Initialisation helper
#define init_alloc(n) (init((WORD *)calloc((n), WORD_SIZE), (n), DEFAULT_STACK_SIZE, DEFAULT_STACK_SIZE))

// Memory access

#define STACK_DIRECTION 1
#define _LOAD_WORD(a, temp)                                             \
    ((exception = exception ? exception : load_word(S, (a), &temp)), temp)
#define LOAD_WORD(a) _LOAD_WORD(a, temp)
#define STORE_WORD(a, v)                                                \
    (exception = exception ? exception : store_word(S, (a), (v)))
#define LOAD_BYTE(a)                                                    \
    ((exception = exception ? exception : load_byte(S, (a), &byte)), byte)
#define STORE_BYTE(a, v)                                                \
    (exception = exception ? exception : store_byte(S, (a), (v)))
#define PUSH(v)                                 \
    (S->SP += WORD_SIZE * STACK_DIRECTION, STORE_WORD(S->SP, (v)))
#define POP                                     \
    (S->SP -= WORD_SIZE * STACK_DIRECTION, LOAD_WORD(S->SP + WORD_SIZE * STACK_DIRECTION))
#if WORD_SIZE == 4
#define PUSH64(ud)                              \
    PUSH((UWORD)(ud & WORD_MASK));              \
    PUSH((UWORD)((ud >> WORD_BIT) & WORD_MASK))
#define POP64                                   \
    (S->SP -= 2 * WORD_SIZE * STACK_DIRECTION, (UWORD)LOAD_WORD(S->SP + WORD_SIZE * STACK_DIRECTION), temp | \
     ((uint64_t)(UWORD)_LOAD_WORD(S->SP + 2 * WORD_SIZE * STACK_DIRECTION, temp2) << WORD_BIT))
#elif WORD_SIZE == 8
#define PUSH64 PUSH
#define POP64  POP
#else
#error "WORD_SIZE is not 4 or 8!"
#endif
#define PUSH_RETURN(v)                          \
    (S->RP += WORD_SIZE * STACK_DIRECTION, STORE_WORD(S->RP, (v)))
#define POP_RETURN                              \
    (S->RP -= WORD_SIZE * STACK_DIRECTION, LOAD_WORD(S->RP + WORD_SIZE * STACK_DIRECTION))
#define STACK_UNDERFLOW(ptr, base)              \
    (ptr - base == 0 ? false : (STACK_DIRECTION > 0 ? ptr < base : ptr > base))

#define PUSH_NATIVE_POINTER(p)                                          \
    {                                                                   \
        WORD_pointer wp = { .pointer = p };                             \
        for (unsigned i = 0; i < NATIVE_POINTER_SIZE / WORD_SIZE; i++)  \
            PUSH(wp.words[i]);                                          \
    }
#define POP_NATIVE_POINTER(p)                                           \
    {                                                                   \
        WORD_pointer wp;                                                \
        for (int i = (NATIVE_POINTER_SIZE / WORD_SIZE) - 1; i >= 0; i--) \
            wp.words[i] = POP;                                          \
        p = wp.pointer;                                                 \
    }

uint8_t *native_address_range_in_one_area(state *S, UWORD start, UWORD length, bool writable);

// Align a VM address
#define ALIGN(a) ((a + WORD_SIZE - 1) & (-WORD_SIZE))

// Check whether a VM address is aligned
#define IS_ALIGNED(a)     (((a) & (WORD_SIZE - 1)) == 0)

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#define ARSHIFT(n, p) (((n) >> (p)) | ((typeof(n))(-((n) < 0)) << (WORD_BIT - (p))))

ptrdiff_t encode_instruction_native(BYTE *addr, enum instruction_type type, WORD v);
ptrdiff_t encode_instruction(state *S, UWORD *addr, enum instruction_type type, WORD v);
ptrdiff_t decode_instruction_file(FILE *file, WORD *val);
ptrdiff_t decode_instruction(state *S, UWORD *addr, WORD *val);

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
