// Manage storage for the state, registers and memory.
//
// (c) Mit authors 1994-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "safe-alloc.h"

#include "mit/mit.h"

#include "state.h"


// Constants
const unsigned mit_word_bytes = MIT_WORD_BYTES;
const unsigned mit_endism = MIT_ENDISM;
const unsigned mit_size_word = MIT_SIZE_WORD;
const unsigned mit_byte_bit = 8;
const unsigned mit_byte_mask = MIT_BYTE_MASK;
const unsigned mit_word_bit = MIT_WORD_BIT;
const mit_uword mit_word_mask = MIT_WORD_MASK;
const mit_uword mit_uword_max = MIT_UWORD_MAX;
const mit_word mit_word_min = MIT_WORD_MIN;
const mit_word mit_word_max = MIT_WORD_MAX;
const unsigned mit_opcode_bit = MIT_OPCODE_BIT;
const unsigned mit_opcode_mask = MIT_OPCODE_MASK;


// Utility functions

_GL_ATTRIBUTE_CONST mit_uword mit_align(mit_uword addr, unsigned size)
{
    return align(addr, size);
}

_GL_ATTRIBUTE_CONST int mit_is_aligned(mit_uword addr, unsigned size)
{
    return is_aligned(addr, size);
}


// Memory

_GL_ATTRIBUTE_PURE uint8_t *mit_native_address_of_range(mit_state *S, mit_uword addr, mit_uword len)
{
    return native_address_of_range(S->memory, S->memory_words, addr, len);
}

int mit_load(mit_state *S, mit_uword addr, unsigned size, mit_word *val_ptr)
{
    return load(S->memory, S->memory_words, addr, size, val_ptr);
}

int mit_store(mit_state *S, mit_uword addr, unsigned size, mit_word val)
{
    return store(S->memory, S->memory_words, addr, size, val);
}


// Stacks

int mit_load_stack(mit_state *S, mit_uword pos, mit_word *val_ptr)
{
    return load_stack(S->stack, S->stack_depth, pos, val_ptr);
}

int mit_store_stack(mit_state *S, mit_uword pos, mit_word val)
{
    return store_stack(S->stack, S->stack_depth, pos, val);
}

int mit_pop_stack(mit_state *S, mit_word *val_ptr)
{
    int ret = load_stack(S->stack, S->stack_depth, 0, val_ptr);
    S->stack_depth--;
    return ret;
}

int mit_push_stack(mit_state *S, mit_word val)
{
    if (unlikely(S->stack_depth >= S->stack_words))
        return MIT_ERROR_STACK_OVERFLOW;

    (S->stack_depth)++;
    return store_stack(S->stack, S->stack_depth, 0, val);
}


// Initialisation and memory management

mit_state *mit_new_state(size_t memory_words, size_t stack_words)
{
    mit_state *S = calloc(1, sizeof(mit_state));
    if (S == NULL)
        return NULL;

    if (memory_words > 0 &&
        (S->memory = calloc(memory_words, sizeof(mit_word))) == NULL)
        return NULL;

    if (stack_words > 0 &&
        (S->stack = calloc(stack_words, sizeof(mit_word))) == NULL) {
        FREE(S->memory);
        return NULL;
    }

    S->pc = 0;
    S->stack_depth = 0;
    S->memory_words = memory_words;
    S->stack_words = stack_words;

    return S;
}

void mit_free_state(mit_state *S)
{
    free(S->memory);
    free(S->stack);
    free(S);
}

#define R_RO(reg, type, return_type)                                \
    _GL_ATTRIBUTE_PURE return_type mit_get_ ## reg(mit_state *S) {  \
        return S->reg;                                              \
    }

#define R(reg, type, return_type)                                   \
    R_RO(reg, type, return_type)                                    \
    void mit_set_ ## reg(mit_state *S, type val) {                  \
        S->reg = val;                                               \
    }
#include "mit/registers.h"
#undef R
#undef R_RO
