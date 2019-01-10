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
#define MAX_MEMORY (((UWORD)1 << (word_bit - 1)) / word_size) // Maximum size of memory in words (half the address space)

// Stacks
extern const int stack_direction;
#define MAX_STACK_SIZE       ((((UWORD)1) << (word_bit - 4)) / word_size)
#define DEFAULT_STACK_SIZE   ((UWORD)16384U)

#define PUSH(v)                                                         \
    (exception == 0 ? push_stack(&(S->SP), S->S0, S->SSIZE, v) : exception)
#define POP(v)                                                          \
    (exception == 0 ? pop_stack(&(S->SP), S->S0, S->SSIZE, v) : exception)

#define PUSH_NATIVE_TYPE(ty, v)                                         \
    for (unsigned i = 0; i < align(sizeof(ty)) / word_size; i++) {      \
        PUSH((UWORD)((size_t)v & word_mask));                           \
        v = (ty)((size_t)v >> word_bit);                                \
    }
#define POP_NATIVE_TYPE(ty, v)                                          \
    *v = 0;                                                             \
    for (unsigned i = 0; i < align(sizeof(ty)) / word_size; i++) {      \
        WORD w;                                                         \
        POP(&w);                                                        \
        *v = (ty)(((size_t)(*v) << word_bit) | w);                      \
    }

// Align a VM address
UWORD align(UWORD addr);

// Check whether a VM address is aligned
bool is_aligned(UWORD addr);

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#define ARSHIFT(n, p) (((n) >> (p)) | ((typeof(n))(-((n) < 0)) << (word_bit - (p))))

// Bit utilities
_GL_ATTRIBUTE_CONST int find_msbit(WORD v); // return msbit of a WORD
int byte_size(WORD v); // return number of significant bytes in a WORD quantity

// Initialisation helper
state *init_default_stacks(size_t memory_size);

// Instructions
#define INSTRUCTION_CHUNK_BIT 6
#define INSTRUCTION_CHUNK_MASK ((1 << INSTRUCTION_CHUNK_BIT) - 1)
#define INSTRUCTION_MAX_CHUNKS (((word_bit + INSTRUCTION_CHUNK_BIT - 1) / INSTRUCTION_CHUNK_BIT))
ptrdiff_t encode_instruction_native(BYTE *addr, enum instruction_type type, WORD v);
ptrdiff_t encode_instruction(state *S, UWORD addr, enum instruction_type type, WORD v);
ptrdiff_t decode_instruction_file(int fd, WORD *val);
ptrdiff_t decode_instruction(state *S, UWORD *addr, WORD *val);

// Object files
#define MAGIC_LENGTH 8


#endif
