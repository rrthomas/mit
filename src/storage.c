// Allocate storage for the registers and memory.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "smite.h"
#include "aux.h"


// Constants
const unsigned smite_word_size = WORD_SIZE;
const unsigned smite_byte_bit = 8;
const unsigned smite_byte_mask = (1 << smite_BYTE_BIT) - 1;
const unsigned smite_word_bit = WORD_SIZE * smite_BYTE_BIT;
#if WORD_SIZE == 4
const smite_UWORD smite_word_mask = UINT32_MAX;
const smite_UWORD smite_uword_max = UINT32_MAX;
const smite_WORD smite_word_min = INT32_MIN;
const smite_WORD smite_word_max = INT32_MAX;
#elif WORD_SIZE == 8
const smite_UWORD smite_word_mask = UINT64_MAX;
const smite_UWORD smite_uword_max = UINT64_MAX;
const smite_WORD smite_word_min = INT64_MIN;
const smite_WORD smite_word_max = INT64_MAX;
#else
#error "WORD_SIZE is not 4 or 8!"
#endif
const int smite_stack_direction = 1;


// Utility functions

_GL_ATTRIBUTE_CONST smite_UWORD smite_align(smite_UWORD addr)
{
    return (addr + smite_word_size - 1) & -smite_word_size;
}

_GL_ATTRIBUTE_CONST int smite_is_aligned(smite_UWORD addr)
{
    return (addr & (smite_word_size - 1)) == 0;
}

// General memory access

_GL_ATTRIBUTE_PURE uint8_t *smite_native_address_of_range(smite_state *S, smite_UWORD addr, smite_UWORD length)
{
    if (addr >= S->MEMORY || length > S->MEMORY - addr)
        return NULL;
    return ((uint8_t *)(S->memory)) + addr;
}

int smite_load_word(smite_state *S, smite_UWORD addr, smite_WORD *value)
{
    if (addr >= S->MEMORY) {
        S->BAD_ADDRESS = addr;
        return -5;
    }
    if (!smite_is_aligned(addr)) {
        S->BAD_ADDRESS = addr;
        return -7;
    }

    *value = S->memory[addr / smite_word_size];
    return 0;
}

int smite_load_byte(smite_state *S, smite_UWORD addr, smite_BYTE *value)
{
    if (addr >= S->MEMORY) {
        S->BAD_ADDRESS = addr;
        return -5;
    }

    *value = ((uint8_t *)(S->memory))[addr];
    return 0;
}

int smite_store_word(smite_state *S, smite_UWORD addr, smite_WORD value)
{
    if (addr >= S->MEMORY) {
        S->BAD_ADDRESS = addr;
        return -6;
    }
    if (!smite_is_aligned(addr)) {
        S->BAD_ADDRESS = addr;
        return -7;
    }

    S->memory[addr / smite_word_size] = value;
    return 0;
}

int smite_store_byte(smite_state *S, smite_UWORD addr, smite_BYTE value)
{
    if (addr >= S->MEMORY) {
        S->BAD_ADDRESS = addr;
        return -6;
    }

    ((uint8_t *)(S->memory))[addr] = value;
    return 0;
}


// Stacks

int smite_load_stack(smite_state *S, smite_UWORD pos, smite_WORD *vp)
{
    if (pos >= S->STACK_DEPTH) {
        S->BAD_ADDRESS = pos;
        return -3;
    }

    UNCHECKED_LOAD_STACK(pos, vp);
    return 0;
}

int smite_store_stack(smite_state *S, smite_UWORD pos, smite_WORD v)
{
    if (pos >= S->STACK_DEPTH) {
        S->BAD_ADDRESS = pos;
        return -4;
    }

    UNCHECKED_STORE_STACK(pos, v);
    return 0;
}

int smite_pop_stack(smite_state *S, smite_WORD *v)
{
    int ret = smite_load_stack(S, 0, v);
    S->STACK_DEPTH--;
    return ret;
}

int smite_push_stack(smite_state *S, smite_WORD v)
{
    if (S->STACK_DEPTH == S->STACK_SIZE) {
        S->BAD_ADDRESS = S->STACK_SIZE;
        return -2;
    }

    (S->STACK_DEPTH)++;
    return smite_store_stack(S, 0, v);
}

int smite_rotate_stack(smite_state *S, smite_WORD pos)
{
    if (pos > 0) {
        if (pos >= (smite_WORD)S->STACK_DEPTH) {
            S->BAD_ADDRESS = pos;
            return -3;
        }

        smite_UWORD offset = S->STACK_DEPTH - pos - 1;
        smite_WORD temp = *(S->S0 + offset * smite_stack_direction);
        memmove(S->S0 + offset * smite_stack_direction,
                S->S0 + (offset + 1) * smite_stack_direction,
                (S->STACK_DEPTH - offset) * sizeof(smite_WORD));
        *(S->S0 + (S->STACK_DEPTH - 1) * smite_stack_direction) = temp;
    } else if (pos < 0) {
        if (pos <= -(smite_WORD)S->STACK_DEPTH) {
            S->BAD_ADDRESS = -pos;
            return -3;
        }

        smite_UWORD offset = S->STACK_DEPTH + pos - 1;
        smite_WORD temp = *(S->S0 + (S->STACK_DEPTH - 1) * smite_stack_direction);
        memmove(S->S0 + (offset + 1) * smite_stack_direction,
                S->S0 + offset * smite_stack_direction,
                (S->STACK_DEPTH - offset) * sizeof(smite_WORD));
        *(S->S0 + offset * smite_stack_direction) = temp;
    }

    return 0;
}


// Initialisation and memory management

static int smite_realloc(smite_WORD **ptr, smite_UWORD old_size, smite_UWORD new_size)
{
    smite_WORD *new_ptr = realloc(*ptr, new_size * smite_word_size);
    if (new_ptr == NULL)
        return -1;
    *ptr = new_ptr;

    if (old_size < new_size)
        memset(*ptr + old_size, 0, (new_size - old_size) * smite_word_size);

    return 0;
}

int smite_realloc_memory(smite_state *S, smite_UWORD size)
{
    int ret = smite_realloc(&S->memory, S->MEMORY / smite_word_size, size);
    if (ret == 0)
        S->MEMORY = size * smite_word_size;
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
    S->BAD_PC = 0;
    S->BAD_ADDRESS = 0;
    S->I = 0;
    S->STACK_DEPTH = 0;

    return S;
}

void smite_destroy(smite_state *S)
{
    free(S->memory);
    free(S->S0);
    free(S->main_argv_len);
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
#include "register-list.h"
#undef R
#undef R_RO
