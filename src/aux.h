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


// VM registers
struct _state {
#define R(reg, type, utype) type reg;
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "tbl_registers.h"
#undef R
#undef R_RO
    WORD *memory;
    WORD *d_stack;
    WORD *r_stack;
    UWORD here;	// (FIXME: debug.c) where the next instruction will be stored
    int main_argc;
    char **main_argv;
    UWORD *main_argv_len;
};

// Memory size
#define DEFAULT_MEMORY ((UWORD)0x100000U) // Default size of VM memory in words
#define MAX_MEMORY (((UWORD)1 << (WORD_BIT - 1)) / WORD_SIZE) // Maximum size of memory in words (half the address space)

// Stack sizes
#define MAX_STACK_SIZE       ((((UWORD)1) << (WORD_BIT - 4)) / WORD_SIZE)
#define DEFAULT_STACK_SIZE   ((UWORD)16384U)

// Initialisation helper
state *init_default_stacks(size_t memory_size);

// Memory access

#define STACK_DIRECTION 1
#define LOAD_STACK(sp, base, size, n)                                   \
    (STACK_VALID((sp), (base), (size)) ? (sp)[-n * STACK_DIRECTION] : (exception = -9))
#define STORE_STACK(sp, base, size, n, v)                               \
    (STACK_VALID((sp) - n, (base), (size)) ? (sp)[-n * STACK_DIRECTION] = (v) :           \
       (exception = -9))
#define _PUSH_STACK(sp, base, size, v)                                  \
    sp += STACK_DIRECTION,                                              \
     STORE_STACK(sp, base, size, 0, v)
#define PUSH_STACK(sp, base, size, v)                                   \
    (exception == 0 ? _PUSH_STACK(sp, base, size, v) : exception)
#define POP_STACK(sp, base, size)                                       \
    (exception == 0 ? (sp -= STACK_DIRECTION,                           \
     LOAD_STACK(sp, base, size, -STACK_DIRECTION)) : exception)
#define PUSH(v) PUSH_STACK(S->SP, S->S0, S->SSIZE, v)
#define POP     POP_STACK(S->SP, S->S0, S->SSIZE)
#if WORD_SIZE == 4
#define PUSH64(ud)                              \
    PUSH((UWORD)(ud & WORD_MASK));              \
    PUSH((UWORD)((ud >> WORD_BIT) & WORD_MASK))
#define POP64                                   \
    (S->SP -= 2 * STACK_DIRECTION, (UWORD)*(S->SP + STACK_DIRECTION) | \
     ((uint64_t)(UWORD)*(S->SP + 2 * STACK_DIRECTION) << WORD_BIT))
#elif WORD_SIZE == 8
#define PUSH64 PUSH
#define POP64  POP
#else
#error "WORD_SIZE is not 4 or 8!"
#endif
#define STACK_UNDERFLOW(ptr, base)              \
    (ptr == base ? false : (STACK_DIRECTION > 0 ? (ptr < base) : (ptr > base)))
#define STACK_OVERFLOW(ptr, base, size)         \
    (ptr == base ? false : ((UWORD)(STACK_DIRECTION > 0 ? (ptr - base) : (base - ptr)) > size))
#define STACK_VALID(ptr, base, size)            \
    (!STACK_UNDERFLOW((ptr), (base)) && !STACK_OVERFLOW((ptr), (base), (size)))

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

// Align a VM address
#define ALIGN(a) ((a + WORD_SIZE - 1) & (-WORD_SIZE))

// Check whether a VM address is aligned
#define IS_ALIGNED(a)     (((a) & (WORD_SIZE - 1)) == 0)

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#define ARSHIFT(n, p) (((n) >> (p)) | ((typeof(n))(-((n) < 0)) << (WORD_BIT - (p))))

ptrdiff_t encode_instruction_native(BYTE *addr, enum instruction_type type, WORD v);
ptrdiff_t encode_instruction(state *S, UWORD addr, enum instruction_type type, WORD v);
ptrdiff_t decode_instruction_file(int fd, WORD *val);
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
