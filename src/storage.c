// Allocate storage for the registers and memory.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "smite.h"
#include "aux.h"


// Constants
const unsigned smite_word_size = WORD_SIZE;
const unsigned smite_native_pointer_size = (unsigned)sizeof(void *);
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
smite_UWORD smite_default_memory_size = 0x100000U; // Default size of VM memory in words
smite_UWORD smite_max_memory_size = ((smite_UWORD)1 << (WORD_SIZE * smite_BYTE_BIT - 1)) / WORD_SIZE; // Maximum size of memory in words (half the address space)
smite_UWORD smite_max_stack_size = (((smite_UWORD)1) << (WORD_SIZE * smite_BYTE_BIT - 4)) / WORD_SIZE;
smite_UWORD smite_default_stack_size = 16384U;


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
    if (addr >= S->MEMORY)
        return -9;
    if (!smite_is_aligned(addr))
        return -23;

    *value = S->memory[addr / smite_word_size];
    return 0;
}

int smite_load_byte(smite_state *S, smite_UWORD addr, smite_BYTE *value)
{
    if (addr >= S->MEMORY)
        return -9;

    *value = ((uint8_t *)(S->memory))[addr];
    return 0;
}

int smite_store_word(smite_state *S, smite_UWORD addr, smite_WORD value)
{
    if (addr >= S->MEMORY)
        return -9;
    if (!smite_is_aligned(addr))
        return -23;

    S->memory[addr / smite_word_size] = value;
    return 0;
}

int smite_store_byte(smite_state *S, smite_UWORD addr, smite_BYTE value)
{
    if (addr >= S->MEMORY)
        return -9;

    ((uint8_t *)(S->memory))[addr] = value;
    return 0;
}


// Stacks

int smite_load_stack(smite_state *S, smite_UWORD pos, smite_WORD *v)
{
    if (pos >= S->STACK_DEPTH)
        return -9;

    *v = *(S->S0 + (S->STACK_DEPTH - pos - 1) * smite_stack_direction);
    return 0;
}

int smite_store_stack(smite_state *S, smite_UWORD pos, smite_WORD v)
{
    if (pos >= S->STACK_DEPTH)
        return -9;

    *(S->S0 + (S->STACK_DEPTH - pos - 1) * smite_stack_direction) = v;
    return 0;
}

int smite_pop_stack(smite_state *S, smite_WORD *v)
{
    if (S->STACK_DEPTH == 0)
        return -9;

    int ret = smite_load_stack(S, 0, v);
    S->STACK_DEPTH--;
    return ret;
}

int smite_push_stack(smite_state *S, smite_WORD v)
{
    if (S->STACK_DEPTH == S->STACK_SIZE)
        return -9;

    (S->STACK_DEPTH)++;
    return smite_store_stack(S, 0, v);
}


// Initialisation and memory management

int smite_mem_realloc(smite_state *S, smite_UWORD size)
{
    if (size > smite_uword_max / smite_word_size)
        return -1;

    S->memory = realloc(S->memory, size * smite_word_size);
    if (S->memory == NULL)
        return -1;

    if (S->MEMORY < size)
        memset(S->memory + S->MEMORY, 0, (size - S->MEMORY) * smite_word_size);
    S->MEMORY = size * smite_word_size;

    return 0;
}


smite_state *smite_init(size_t size, size_t data_stack_size)
{
    if (size > smite_max_memory_size || data_stack_size > smite_max_stack_size)
        return NULL;

    smite_state *S = calloc(1, sizeof(smite_state));
    if (S == NULL)
        return NULL;

    if (smite_mem_realloc(S, size) != 0)
        return NULL;

    S->STACK_SIZE = data_stack_size;
    S->S0 = calloc(S->STACK_SIZE, smite_word_size);
    if (S->S0 == NULL)
        return NULL;

    S->ENDISM =
#ifdef smite_WORDS_BIGENDIAN
        1
#else
        0
#endif
        ;
    S->PC = 0;
    S->I = 0;
    S->STACK_DEPTH = 0;

    return S;
}

smite_state *smite_init_default_stacks(size_t memory_size)
{
    return smite_init(memory_size, smite_default_stack_size);
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
