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

#include "external-syms.h"

#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "public.h"
#include "aux.h"


// Constants
const UWORD word_size = WORD_SIZE;
const UWORD native_pointer_size = sizeof(void *);
const UWORD byte_bit = 8;
const UWORD byte_mask = (1 << BYTE_BIT) - 1;
const UWORD word_bit = WORD_SIZE * BYTE_BIT;
#if WORD_SIZE == 4
const UWORD word_mask = UINT32_MAX;
const UWORD uword_max = UINT32_MAX;
const WORD word_min = INT32_MIN;
// FIXME: add uword_min, word_max
#elif WORD_SIZE == 8
const UWORD word_mask = UINT64_MAX;
const UWORD uword_max = UINT64_MAX;
const WORD word_min = INT64_MIN;
// FIXME: add uword_min, word_max
#else
#error "WORD_SIZE is not 4 or 8!"
#endif
const int stack_direction = 1;


// Utility functions

_GL_ATTRIBUTE_CONST UWORD align(UWORD addr)
{
    return (addr + word_size - 1) & -word_size;
}

_GL_ATTRIBUTE_CONST int is_aligned(UWORD addr)
{
    return (addr & (word_size - 1)) == 0;
}

// General memory access

_GL_ATTRIBUTE_PURE uint8_t *native_address_of_range(state *S, UWORD addr, UWORD length)
{
    if (addr >= S->MEMORY || length > S->MEMORY - addr)
        return NULL;
    return ((uint8_t *)(S->memory)) + addr;
}

int load_word(state *S, UWORD addr, WORD *value)
{
    if (addr >= S->MEMORY) {
        S->INVALID = addr;
        return -9;
    }
    if (!is_aligned(addr)) {
        S->INVALID = addr;
        return -23;
    }

    *value = S->memory[addr / word_size];
    return 0;
}

int load_byte(state *S, UWORD addr, BYTE *value)
{
    if (addr >= S->MEMORY) {
        S->INVALID = addr;
        return -9;
    }

    *value = ((uint8_t *)(S->memory))[addr];
    return 0;
}

int store_word(state *S, UWORD addr, WORD value)
{
    if (addr >= S->MEMORY) {
        S->INVALID = addr;
        return -9;
    }
    if (!is_aligned(addr)) {
        S->INVALID = addr;
        return -23;
    }

    S->memory[addr / word_size] = value;
    return 0;
}

int store_byte(state *S, UWORD addr, BYTE value)
{
    if (addr >= S->MEMORY) {
        S->INVALID = addr;
        return -9;
    }

    ((uint8_t *)(S->memory))[addr] = value;
    return 0;
}


// Stacks

int load_stack(state *S, UWORD pos, WORD *v)
{
    if (pos >= S->SDEPTH)
        return -9;

    *v = *(S->S0 + (S->SDEPTH - pos - 1) * stack_direction);
    return 0;
}

int store_stack(state *S, UWORD pos, WORD v)
{
    if (pos >= S->SDEPTH)
        return -9;

    *(S->S0 + (S->SDEPTH - pos - 1) * stack_direction) = v;
    return 0;
}

int pop_stack(state *S, WORD *v)
{
    if (S->SDEPTH == 0)
        return -9;

    int ret = load_stack(S, 0, v);
    S->SDEPTH--;
    return ret;
}

int push_stack(state *S, WORD v)
{
    if (S->SDEPTH == S->SSIZE)
        return -9;

    (S->SDEPTH)++;
    return store_stack(S, 0, v);
}


int load_return_stack(state *S, UWORD pos, WORD *v)
{
    if (pos >= S->RDEPTH)
        return -9;

    *v = *(S->R0 + (S->RDEPTH - pos - 1) * stack_direction);
    return 0;
}

int store_return_stack(state *S, UWORD pos, WORD v)
{
    if (pos >= S->RDEPTH)
        return -9;

    *(S->R0 + (S->RDEPTH - pos - 1) * stack_direction) = v;
    return 0;
}

int pop_return_stack(state *S, WORD *v)
{
    if (S->RDEPTH == 0)
        return -9;

    int ret = load_return_stack(S, 0, v);
    (S->RDEPTH)--;
    return ret;
}

int push_return_stack(state *S, WORD v)
{
    if (S->RDEPTH == S->RSIZE)
        return -9;

    (S->RDEPTH)++;
    return store_return_stack(S, 0, v);
}


// Initialisation and memory management

int mem_realloc(state *S, UWORD size)
{
    if (size > uword_max / word_size)
        return -1;

    S->memory = realloc(S->memory, size * word_size);
    if (S->memory == NULL)
        return -1;

    if (S->MEMORY < size)
        memset(S->memory + S->MEMORY, 0, (size - S->MEMORY) * word_size);
    S->MEMORY = size * word_size;

    return 0;
}


state *init(size_t size, size_t data_stack_size, size_t return_stack_size)
{
    state *S = calloc(1, sizeof(state));
    if (S == NULL)
        return NULL;

    if (mem_realloc(S, size) != 0)
        return NULL;

    S->SSIZE = data_stack_size;
    S->S0 = calloc(S->SSIZE, word_size);
    S->RSIZE = return_stack_size;
    S->R0 = calloc(S->RSIZE, word_size);
    if (S->S0 == NULL || S->R0 == NULL)
        return NULL;

    S->ENDISM =
#ifdef WORDS_BIGENDIAN
        1
#else
        0
#endif
        ;
    S->PC = 0;
    S->I = 0;
    S->SDEPTH = 0;
    S->RDEPTH = 0;
    S->HANDLER = 0;
    S->BADPC = 0;
    S->INVALID = 0;

    return S;
}

state *init_default_stacks(size_t memory_size)
{
    return init(memory_size, DEFAULT_STACK_SIZE, DEFAULT_STACK_SIZE);
}

void destroy(state *S)
{
    free(S->memory);
    free(S->S0);
    free(S->R0);
    free(S->main_argv_len);
    free(S);
}

#define R_RO(reg, type, utype)                          \
    _GL_ATTRIBUTE_PURE type get_ ## reg(state *S) {     \
        return S->reg;                                  \
    }
#define R(reg, type, utype)                         \
    R_RO(reg, type, utype)                          \
    void set_ ## reg(state *S, type value) {        \
        S->reg = value;                             \
    }
#include "register-list.h"
#undef R
#undef R_RO
