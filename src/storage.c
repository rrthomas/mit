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

#include "external_syms.h"

#include <stdlib.h>
#include <string.h>

#include "public.h"
#include "aux.h"


unsigned word_size = WORD_SIZE;


_GL_ATTRIBUTE_PURE UWORD mem_here(state *S)
{
    return S->_mem_here;
}

UWORD mem_align(state *S)
{
    return S->_mem_here = ALIGN(S->_mem_here);
}

_GL_ATTRIBUTE_PURE uint8_t *native_address_of_range(state *S, UWORD addr, UWORD length)
{
    if (addr >= S->MEMORY || length > S->MEMORY - addr)
        return NULL;
    return ((uint8_t *)(S->memory)) + addr;
}

int mem_realloc(state *S, UWORD size)
{
    if (size > UWORD_MAX / WORD_SIZE)
        return -1;

    S->memory = realloc(S->memory, size * WORD_SIZE);
    if (S->memory == NULL)
        return -1;

    if (S->MEMORY < size)
        memset(S->memory + S->MEMORY, 0, (size - S->MEMORY) * WORD_SIZE);
    S->MEMORY = size * WORD_SIZE;

    return 0;
}


// General memory access

int load_word(state *S, UWORD addr, WORD *value)
{
    if (addr >= S->MEMORY) {
        S->INVALID = addr;
        return -9;
    }
    if (!IS_ALIGNED(addr)) {
        S->INVALID = addr;
        return -23;
    }

    *value = S->memory[addr / WORD_SIZE];
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
    if (!IS_ALIGNED(addr)) {
        S->INVALID = addr;
        return -23;
    }

    S->memory[addr / WORD_SIZE] = value;
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


state *init(size_t size, size_t data_stack_size, size_t return_stack_size)
{
    state *S = calloc(1, sizeof(state));
    if (S == NULL)
        return NULL;

    if (mem_realloc(S, size) != 0)
        return NULL;

    S->_mem_here = 0UL;

    S->SSIZE = data_stack_size;
    S->d_stack = calloc(S->SSIZE, WORD_SIZE);
    S->RSIZE = return_stack_size;
    S->r_stack = calloc(S->RSIZE, WORD_SIZE);
    if (S->d_stack == NULL || S->r_stack == NULL)
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
    S->S0 = S->SP = S->d_stack;
    S->R0 = S->RP = S->r_stack;
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
    if (S) {
        free(S->memory);
        free(S->d_stack);
        free(S->r_stack);
        free(S->main_argv_len);
        free(S);
    }
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
#include "tbl_registers.h"
#undef R
#undef R_RO
