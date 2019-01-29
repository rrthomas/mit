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

#ifndef SMITE_AUX
#define SMITE_AUX


#include <stdio.h>      // for the FILE type
#include <stdint.h>
#include <limits.h>

#include "opcodes.h"


// VM registers
struct _smite_state {
#define R(reg, type, utype) type reg;
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "register-list.h"
#undef R
#undef R_RO
    smite_WORD *memory;
    int halt_code;
    int exception;
    int main_argc;
    char **main_argv;
    smite_UWORD *main_argv_len;
};

// Memory size
extern smite_UWORD smite_default_memory_size;
extern smite_UWORD smite_max_memory_size;

// Stacks
extern const int smite_stack_direction;
extern smite_UWORD smite_default_stack_size;
extern smite_UWORD smite_max_stack_size;

#define POP(v)                                                          \
    (S->exception == 0 ? smite_pop_stack(S, v) : S->exception)
#define PUSH(v)                                                         \
    (S->exception == 0 ? smite_push_stack(S, v) : S->exception)

#define PUSH_NATIVE_TYPE(ty, v)                                         \
    for (unsigned i = 0; i < smite_align(sizeof(ty)) / smite_word_size; i++) { \
        PUSH((smite_UWORD)((size_t)v & smite_word_mask));               \
        v = (ty)((size_t)v >> smite_word_bit);                          \
    }
#define POP_NATIVE_TYPE(ty, v)                                          \
    *v = 0;                                                             \
    for (unsigned i = 0; i < smite_align(sizeof(ty)) / smite_word_size; i++) { \
        smite_WORD w;                                                   \
        POP(&w);                                                        \
        *v = (ty)(((size_t)(*v) << smite_word_bit) | (smite_UWORD)w);   \
    }

// Align a VM address
smite_UWORD smite_align(smite_UWORD addr);

// Check whether a VM address is aligned
int smite_is_aligned(smite_UWORD addr);

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#define ARSHIFT(n, p) (((n) >> (p)) | ((smite_UWORD)(-((smite_WORD)(n) < 0)) << (smite_word_bit - (p))))

// Bit utilities
_GL_ATTRIBUTE_CONST int smite_find_msbit(smite_WORD v); // return msbit of a smite_WORD
int smite_byte_size(smite_WORD v); // return number of significant bytes in a smite_WORD quantity

// Initialisation helper
smite_state *smite_init_default_stacks(size_t memory_size);

// Instructions
#define INSTRUCTION_CHUNK_BIT 6
#define INSTRUCTION_CONTINUATION_BIT (1 << INSTRUCTION_CHUNK_BIT)
#define INSTRUCTION_ACTION_BIT (1 << (INSTRUCTION_CHUNK_BIT + 1))
#define INSTRUCTION_CHUNK_MASK ((1 << INSTRUCTION_CHUNK_BIT) - 1)
#define INSTRUCTION_MAX_CHUNKS (((smite_word_bit + INSTRUCTION_CHUNK_BIT - 1) / INSTRUCTION_CHUNK_BIT))
ptrdiff_t smite_encode_instruction_file(int fd, enum instruction_type type, smite_WORD v);
ptrdiff_t smite_encode_instruction(smite_state *S, smite_UWORD addr, enum instruction_type type, smite_WORD v);
int smite_decode_instruction_file(int fd, smite_WORD *val);
int smite_decode_instruction(smite_state *S, smite_UWORD *addr, smite_WORD *val);

// Object files
#define MAGIC_LENGTH 8


#endif
