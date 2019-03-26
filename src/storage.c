// Allocate storage for the registers and memory.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "smite.h"


// Constants
const unsigned smite_word_size = WORD_SIZE;
const unsigned smite_byte_bit = 8;
const unsigned smite_byte_mask = smite_BYTE_MASK;
const unsigned smite_word_bit = smite_WORD_BIT;
const smite_UWORD smite_word_mask = smite_WORD_MASK;
const smite_UWORD smite_uword_max = smite_UWORD_MAX;
const smite_WORD smite_word_min = smite_WORD_MIN;
const smite_WORD smite_word_max = smite_WORD_MAX;


// Utility functions

_GL_ATTRIBUTE_CONST smite_UWORD smite_align(smite_UWORD addr)
{
    return align(addr);
}

_GL_ATTRIBUTE_CONST int smite_is_aligned(smite_UWORD addr)
{
    return is_aligned(addr);
}


// Memory

_GL_ATTRIBUTE_PURE uint8_t *smite_native_address_of_range(smite_state *S, smite_UWORD addr, smite_UWORD length)
{
    return native_address_of_range(S, addr, length);
}

int smite_load_word(smite_state *S, smite_UWORD addr, smite_WORD *value)
{
    return load_word(S, addr, value);
}

int smite_store_word(smite_state *S, smite_UWORD addr, smite_WORD value)
{
    return store_word(S, addr, value);
}

int smite_load_byte(smite_state *S, smite_UWORD addr, smite_BYTE *value)
{
    return load_byte(S, addr, value);
}

int smite_store_byte(smite_state *S, smite_UWORD addr, smite_BYTE value)
{
    return store_byte(S, addr, value);
}


// Stacks

int smite_load_stack(smite_state *S, smite_UWORD pos, smite_WORD *v)
{
    return load_stack(S, pos, v);
}

int smite_store_stack(smite_state *S, smite_UWORD pos, smite_WORD v)
{
    return store_stack(S, pos, v);
}

int smite_pop_stack(smite_state *S, smite_WORD *v)
{
    return pop_stack(S, v);
}

int smite_push_stack(smite_state *S, smite_WORD v)
{
    return push_stack(S, v);
}


// Initialisation and memory management

static int smite_realloc(smite_WORD **ptr, smite_UWORD old_size, smite_UWORD new_size)
{
    smite_WORD *new_ptr = realloc(*ptr, new_size * WORD_SIZE);
    if (new_ptr == NULL && new_size > 0)
        return 1;
    *ptr = new_ptr;

    if (old_size < new_size)
        memset(*ptr + old_size, 0, (new_size - old_size) * WORD_SIZE);

    return SMITE_ERR_OK;
}

int smite_realloc_memory(smite_state *S, smite_UWORD size)
{
    int ret = smite_realloc(&S->memory, S->MEMORY / WORD_SIZE, size);
    if (ret == 0)
        S->MEMORY = size * WORD_SIZE;
    return ret;
}

int smite_realloc_stack(smite_state *S, smite_UWORD size)
{
    int ret = smite_realloc(&S->S0, S->STACK_SIZE, size);
    if (ret == 0)
        S->STACK_SIZE = size;
    return ret;
}

smite_state *smite_init(size_t memory_size, size_t stack_size)
{
    smite_state *S = calloc(1, sizeof(smite_state));
    if (S == NULL)
        return NULL;

    if (smite_realloc_memory(S, memory_size) != 0)
        return NULL;

    if (smite_realloc_stack(S, stack_size) != 0)
        return NULL;

    S->ENDISM =
#ifdef smite_WORDS_BIGENDIAN
        1
#else
        0
#endif
        ;
    S->PC = 0;
    S->BAD = 0;
    S->STACK_DEPTH = 0;

    return S;
}

void smite_destroy(smite_state *S)
{
    free(S->memory);
    free(S->S0);
    free(S);
}

#define R_RO(reg, type, utype)                          \
    _GL_ATTRIBUTE_PURE type smite_get_ ## reg(smite_state *S) {     \
        return S->reg;                                  \
    }
#define R(reg, type, utype)                         \
    R_RO(reg, type, utype)                          \
    void smite_set_ ## reg(smite_state *S, type value) {        \
        S->reg = value;                             \
    }
#include "registers.h"
#undef R
#undef R_RO

// Register command-line args
int smite_register_args(smite_state *S, int argc, char *argv[])
{
    S->main_argc = argc;
    S->main_argv = argv;

    return SMITE_ERR_OK;
}
