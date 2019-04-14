// Manage storage for the state, registers and memory.
//
// (c) SMite authors 1994-2019
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
const smite_UWORD smite_instruction_bit = SMITE_INSTRUCTION_BIT;
const smite_UWORD smite_instruction_mask = SMITE_INSTRUCTION_MASK;


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

_GL_ATTRIBUTE_PURE uint8_t *smite_native_address_of_range(smite_state *S, smite_UWORD addr, smite_UWORD len)
{
    return native_address_of_range(S, addr, len);
}

int smite_load_word(smite_state *S, smite_UWORD addr, smite_WORD *val_ptr)
{
    return load_word(S, addr, val_ptr);
}

int smite_store_word(smite_state *S, smite_UWORD addr, smite_WORD val)
{
    return store_word(S, addr, val);
}

int smite_load_byte(smite_state *S, smite_UWORD addr, smite_BYTE *val_ptr)
{
    return load_byte(S, addr, val_ptr);
}

int smite_store_byte(smite_state *S, smite_UWORD addr, smite_BYTE val)
{
    return store_byte(S, addr, val);
}


// Stacks

int smite_load_stack(smite_state *S, smite_UWORD pos, smite_WORD *val_ptr)
{
    return load_stack(S, pos, val_ptr);
}

int smite_store_stack(smite_state *S, smite_UWORD pos, smite_WORD val)
{
    return store_stack(S, pos, val);
}

int smite_pop_stack(smite_state *S, smite_WORD *val_ptr)
{
    return pop_stack(S, val_ptr);
}

int smite_push_stack(smite_state *S, smite_WORD val)
{
    return push_stack(S, val);
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

int smite_realloc_memory(smite_state *S, smite_UWORD memory_size)
{
    int ret = smite_realloc(&S->memory, S->MEMORY / WORD_SIZE, memory_size);
    if (ret == 0)
        S->MEMORY = memory_size * WORD_SIZE;
    return ret;
}

int smite_realloc_stack(smite_state *S, smite_UWORD stack_size)
{
    int ret = smite_realloc(&S->S0, S->STACK_SIZE, stack_size);
    if (ret == 0)
        S->STACK_SIZE = stack_size;
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

#define R_RO(reg, type, utype)                                      \
    _GL_ATTRIBUTE_PURE type smite_get_ ## reg(smite_state *S) {     \
        return S->reg;                                              \
    }
#define R(reg, type, utype)                                   \
    R_RO(reg, type, utype)                                    \
    void smite_set_ ## reg(smite_state *S, type val) {        \
        S->reg = val;                                         \
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
