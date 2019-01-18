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
#include <stdint.h>
#include <limits.h>

#include "opcodes.h"


// VM registers
struct _state {
#define R(reg, type, utype) type reg;
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "register-list.h"
#undef R
#undef R_RO
    WORD *memory;
    UWORD here;	// (FIXME: debug.c) where the next instruction will be stored
    int main_argc;
    char **main_argv;
    UWORD *main_argv_len;
};

// Memory size
extern UWORD default_memory_size;
extern UWORD max_memory_size;

// Stacks
extern const int stack_direction;
extern UWORD default_stack_size;
extern UWORD max_stack_size;

#define POP(v)                                                          \
    (exception == 0 ? pop_stack(S, v) : exception)
#define PUSH(v)                                                         \
    (exception == 0 ? push_stack(S, v) : exception)

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
int is_aligned(UWORD addr);

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
ptrdiff_t encode_instruction_file(int fd, enum instruction_type type, WORD v);
ptrdiff_t encode_instruction(state *S, UWORD addr, enum instruction_type type, WORD v);
ptrdiff_t decode_instruction_file(int fd, WORD *val);
ptrdiff_t decode_instruction(state *S, UWORD *addr, WORD *val);

// Object files
#define MAGIC_LENGTH 8


#endif
