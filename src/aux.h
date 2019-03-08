// Auxiliary public functions.
// These are undocumented and subject to change.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
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
    int main_argc;
    char **main_argv;
    FILE *trace_fp; // FILE * of trace file, if used
};

// Stacks
#define STACK_DIRECTION 1

#define UNCHECKED_LOAD_STACK(pos, vp)                                   \
    (*(vp) = *(S->S0 + (S->STACK_DEPTH - (pos) - 1) * STACK_DIRECTION))
#define UNCHECKED_STORE_STACK(pos, v)                                   \
    (*(S->S0 + (S->STACK_DEPTH - (pos) - 1) * STACK_DIRECTION) = (v))

// FIXME: These macros should take ENDISM into account and store the
// quantities on the stack in native order (though perhaps not native
// alignment). Current code is correct for ENDISM=0; need to reverse the
// directions of the loops for ENDISM=1. (Generate unrolled loops from
// Python!)
// Note: One might expect casts to smite_UWORD rather than size_t below. The
// latter avoid warnings when the value `v` is a pointer and sizeof(void *)
// > smite_word_size, but the effect (given unsigned sign extension &
// truncation) is identical.
#define UNCHECKED_LOAD_STACK_TYPE(pos, ty, vp)                          \
    *vp = 0;                                                            \
    for (unsigned i = 0; i < smite_align(sizeof(ty)) / smite_word_size; i++) { \
        smite_WORD w;                                                   \
        UNCHECKED_LOAD_STACK(pos - i, &w);                              \
        *vp = (ty)(((size_t)(*vp) << smite_word_bit) | (smite_UWORD)w); \
    }
#define UNCHECKED_STORE_STACK_TYPE(pos, ty, v)                          \
    for (unsigned i = smite_align(sizeof(ty)) / smite_word_size; i > 0; i--) { \
        UNCHECKED_STORE_STACK(pos - i + 1, (smite_UWORD)((size_t)v & smite_word_mask)); \
        v = (ty)((size_t)v >> smite_word_bit);                          \
    }

// Align a VM address
smite_UWORD smite_align(smite_UWORD addr);

// Check whether a VM address is aligned
int smite_is_aligned(smite_UWORD addr);

// Portable arithmetic right shift (the behaviour of >> on signed
// quantities is implementation-defined in C99)
#ifdef HAVE_ARITHMETIC_RSHIFT
#define ARSHIFT(n, p) ((smite_WORD)(n) >> (p))
#else
#define ARSHIFT(n, p) (((n) >> (p)) | ((smite_UWORD)(-((smite_WORD)(n) < 0)) << (smite_word_bit - (p))))
#endif

// Bit utilities
_GL_ATTRIBUTE_CONST int smite_find_msbit(smite_WORD v); // return msbit of a smite_WORD
int smite_byte_size(smite_WORD v); // return number of significant bytes in a smite_WORD quantity

// Instructions
#define INSTRUCTION_CHUNK_BITS 6
#define INSTRUCTION_CHUNK_MASK ((1 << INSTRUCTION_CHUNK_BITS) - 1)
#define INSTRUCTION_CONTINUATION_BIT (1 << INSTRUCTION_CHUNK_BITS)
#define INSTRUCTION_NUMBER_BIT (1 << (INSTRUCTION_CHUNK_BITS + 1))
int smite_encode_instruction(smite_state *S, smite_UWORD *addr, smite_UWORD type, smite_WORD v);
int smite_decode_instruction(smite_state *S, smite_UWORD *addr, smite_UWORD *type, smite_WORD *val);


#endif
