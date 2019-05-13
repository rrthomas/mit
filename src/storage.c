// Manage storage for the state, registers and memory.
//
// (c) Mit authors 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "mit/mit.h"


// Constants
const unsigned mit_word_bytes = mit_WORD_BYTES;
const unsigned mit_endism = mit_ENDISM;
const unsigned mit_size_word = mit_SIZE_WORD;
const unsigned mit_byte_bit = 8;
const unsigned mit_byte_mask = mit_BYTE_MASK;
const unsigned mit_word_bit = mit_WORD_BIT;
const mit_UWORD mit_word_mask = mit_WORD_MASK;
const mit_UWORD mit_uword_max = mit_UWORD_MAX;
const mit_WORD mit_word_min = mit_WORD_MIN;
const mit_WORD mit_word_max = mit_WORD_MAX;
const unsigned mit_instruction_bit = MIT_INSTRUCTION_BIT;
const unsigned mit_instruction_mask = MIT_INSTRUCTION_MASK;


// Utility functions

_GL_ATTRIBUTE_CONST mit_UWORD mit_align(mit_UWORD addr, unsigned size)
{
    return align(addr, size);
}

_GL_ATTRIBUTE_CONST int mit_is_aligned(mit_UWORD addr, unsigned size)
{
    return is_aligned(addr, size);
}


// Memory

_GL_ATTRIBUTE_PURE uint8_t *mit_native_address_of_range(mit_state *S, mit_UWORD addr, mit_UWORD len)
{
    return native_address_of_range(S, addr, len);
}

int mit_load(mit_state *S, mit_UWORD addr, unsigned size, mit_WORD *val_ptr)
{
    return load(S, addr, size, val_ptr);
}

int mit_store(mit_state *S, mit_UWORD addr, unsigned size, mit_WORD val)
{
    return store(S, addr, size, val);
}


// Stacks

int mit_load_stack(mit_state *S, mit_UWORD pos, mit_WORD *val_ptr)
{
    return load_stack(S, pos, val_ptr);
}

int mit_store_stack(mit_state *S, mit_UWORD pos, mit_WORD val)
{
    return store_stack(S, pos, val);
}

int mit_pop_stack(mit_state *S, mit_WORD *val_ptr)
{
    return pop_stack(S, val_ptr);
}

int mit_push_stack(mit_state *S, mit_WORD val)
{
    return push_stack(S, val);
}


// Initialisation and memory management

static int mit_realloc(mit_WORD * restrict *ptr, mit_UWORD old_size, mit_UWORD new_size)
{
    mit_WORD * restrict new_ptr = realloc(*ptr, new_size * mit_WORD_BYTES);
    if (new_ptr == NULL && new_size > 0)
        return -1;
    *ptr = new_ptr;

    if (old_size < new_size)
        memset(*ptr + old_size, 0, (new_size - old_size) * mit_WORD_BYTES);

    return MIT_ERR_OK;
}

int mit_realloc_memory(mit_state *S, mit_UWORD memory_size)
{
    int ret = mit_realloc(&S->memory, S->memory_size / mit_WORD_BYTES, memory_size);
    if (ret == 0)
        S->memory_size = memory_size * mit_WORD_BYTES;
    return ret;
}

int mit_realloc_stack(mit_state *S, mit_UWORD stack_size)
{
    int ret = mit_realloc(&S->stack, S->stack_size, stack_size);
    if (ret == 0)
        S->stack_size = stack_size;
    return ret;
}

mit_state *mit_init(size_t memory_size, size_t stack_size)
{
    mit_state *S = calloc(1, sizeof(mit_state));
    if (S == NULL)
        return NULL;

    if (mit_realloc_memory(S, memory_size) != 0)
        return NULL;

    if (mit_realloc_stack(S, stack_size) != 0)
        return NULL;

    S->PC = 0;
    S->BAD = 0;
    S->STACK_DEPTH = 0;

    return S;
}

void mit_destroy(mit_state *S)
{
    free(S->memory);
    free(S->stack);
    free(S);
}

#define R_RO(reg, type, utype)                                      \
    _GL_ATTRIBUTE_PURE type mit_get_ ## reg(mit_state *S) {         \
        return S->reg;                                              \
    }
#define R(reg, type, utype)                                   \
    R_RO(reg, type, utype)                                    \
    void mit_set_ ## reg(mit_state *S, type val) {            \
        S->reg = val;                                         \
    }
#include "mit/registers.h"
#undef R
#undef R_RO

// Register command-line args
int mit_register_args(mit_state *S, int argc, char *argv[])
{
    S->main_argc = argc;
    S->main_argv = argv;

    return MIT_ERR_OK;
}
