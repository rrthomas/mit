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
const unsigned mit_instruction_bit = MIT_INSTRUCTION_BIT;
const unsigned mit_instruction_mask = MIT_INSTRUCTION_MASK;


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
    return native_address_of_range(S->memory, S->memory_size, addr, len);
}

int mit_load(mit_state *S, mit_uword addr, unsigned size, mit_word *val_ptr)
{
    return load(S->memory, S->memory_size, addr, size, val_ptr);
}

int mit_store(mit_state *S, mit_uword addr, unsigned size, mit_word val)
{
    return store(S->memory, S->memory_size, addr, size, val);
}


// Stacks

int mit_load_stack(mit_state *S, mit_uword pos, mit_word *val_ptr)
{
    return load_stack(S->stack, S->STACK_DEPTH, pos, val_ptr);
}

int mit_store_stack(mit_state *S, mit_uword pos, mit_word val)
{
    return store_stack(S->stack, S->STACK_DEPTH, pos, val);
}

int mit_pop_stack(mit_state *S, mit_word *val_ptr)
{
    int ret = load_stack(S->stack, S->STACK_DEPTH, 0, val_ptr);
    S->STACK_DEPTH--;
    return ret;
}

int mit_push_stack(mit_state *S, mit_word val)
{
    if (unlikely(S->STACK_DEPTH >= S->stack_size))
        return MIT_ERROR_STACK_OVERFLOW;

    (S->STACK_DEPTH)++;
    return store_stack(S->stack, S->STACK_DEPTH, 0, val);
}


// Initialisation and memory management

static int mit_realloc(mit_word * restrict *ptr, mit_uword old_size, mit_uword new_size)
{
    mit_word * restrict new_ptr = realloc(*ptr, new_size * MIT_WORD_BYTES);
    if (new_ptr == NULL && new_size > 0)
        return MIT_MALLOC_ERROR_CANNOT_ALLOCATE_MEMORY;
    *ptr = new_ptr;

    if (old_size < new_size)
        memset(*ptr + old_size, 0, (new_size - old_size) * MIT_WORD_BYTES);

    return MIT_MALLOC_ERROR_OK;
}

int mit_realloc_memory(mit_state *S, mit_uword memory_size)
{
    int ret = mit_realloc(&S->memory, S->memory_size / MIT_WORD_BYTES, memory_size);
    if (ret == 0)
        S->memory_size = memory_size * MIT_WORD_BYTES;
    return ret;
}

int mit_realloc_stack(mit_state *S, mit_uword stack_size)
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

#define R(reg)                                                      \
    _GL_ATTRIBUTE_PURE mit_uword mit_get_ ## reg(mit_state *S) {    \
        return S->reg;                                              \
    }                                                               \
    void mit_set_ ## reg(mit_state *S, mit_uword val) {             \
        S->reg = val;                                               \
    }
#include "mit/registers.h"
#undef R

// Register command-line args
int mit_register_args(mit_state *S, int argc, char *argv[])
{
    S->main_argc = argc;
    S->main_argv = argv;

    return MIT_ERROR_OK;
}
