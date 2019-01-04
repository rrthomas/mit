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
#include "gl_avltree_list.h"

#include "public.h"
#include "aux.h"


unsigned word_size = WORD_SIZE;


// Memory allocation and mapping
typedef struct {
    UWORD start;
    UWORD size;
    uint8_t *ptr;
    bool writable;
} Mem_area;

static int cmp_mem_area(const void *a_, const void *b_)
{
    const Mem_area *a = (const Mem_area *)a_, *b = (const Mem_area *)b_;
    if (a->start + a->size - 1 < b->start)
        return -1;
    else if (a->start > b->start + b->size - 1)
        return 1;
    return 0;
}

static bool eq_mem_area(const void *a_, const void *b_)
{
    return cmp_mem_area(a_, b_) == 0;
}

static void free_mem_area(const void *a)
{
    free((void *)a);
}

_GL_ATTRIBUTE_PURE UWORD mem_here(state *S)
{
    return S->_mem_here;
}

// Given a range of addresses, return Mem_area corresponding to some address
// in that range.
// This is used a) to find the area for a particular word;
//              b) to test whether part of a range has already been allocated
static Mem_area *mem_range(state *S, UWORD start, UWORD length)
{
    Mem_area a_addr = {start, length, NULL, true};
    gl_list_node_t elt = gl_sortedlist_search(S->mem_areas, cmp_mem_area, &a_addr);
    return elt ? (Mem_area *)gl_list_node_value(S->mem_areas, elt) : NULL;
}

#define addr_in_area(a, addr) (a->ptr + ((addr) - a->start))

_GL_ATTRIBUTE_PURE uint8_t *native_address(state *S, UWORD addr, bool write)
{
    Mem_area *a = mem_range(S, addr, 1);
    if (a == NULL || (write && !a->writable))
        return NULL;
    return addr_in_area(a, addr);
}

// Return address of a range iff it falls inside an area
uint8_t *native_address_range_in_one_area(state *S, UWORD start, UWORD length, bool write)
{
    Mem_area *a = mem_range(S, start, 1);
    if (a == NULL || (write && !a->writable) || a->size - (start - a->start) < length)
        return NULL;
    return addr_in_area(a, start);
}

// Map the given native block of memory to VM address addr
static bool mem_map(state *S, UWORD addr, void *p, size_t n, bool writable)
{
    // Return false if area is too big, or covers already-allocated addresses
    if ((addr > 0 && n > (UWORD_MAX - addr + 1)) || mem_range(S, addr, n) != NULL)
        return false;

    Mem_area *area = malloc(sizeof(Mem_area));
    if (area == NULL)
        return false;
    *area = (Mem_area){addr, n, p, writable};

    gl_list_node_t elt = gl_sortedlist_nx_add(S->mem_areas, cmp_mem_area, area);
    if (elt == NULL)
        return false;

    return true;
}

UWORD mem_allot(state *S, void *p, size_t n, bool writable)
{
    if (!mem_map(S, S->_mem_here, p, n, writable))
        return WORD_MASK;

    size_t start = S->_mem_here;
    S->_mem_here += n;
    return start;
}

UWORD mem_align(state *S)
{
    return S->_mem_here = ALIGN(S->_mem_here);
}


// General memory access

int load_word(state *S, UWORD addr, WORD *value)
{
    if (!IS_ALIGNED(addr)) {
        S->INVALID = addr;
        return -23;
    }

    // Aligned access to a single memory area
    uint8_t *ptr = native_address_range_in_one_area(S, addr, WORD_SIZE, false);
    if (ptr != NULL && IS_ALIGNED((size_t)ptr)) {
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wcast-align"
        *value = *(WORD *)ptr;
#pragma GCC diagnostic pop
        return 0;
    }

    // Awkward access
    *value = 0;
    for (unsigned i = 0; i < WORD_SIZE; i++, addr++) {
        ptr = native_address(S, addr, false);
        if (ptr == NULL) {
            S->INVALID = addr;
            return -9;
        }
        ((BYTE *)value)[S->ENDISM ? WORD_SIZE - i : i] = *ptr;
    }
    return 0;
}

int load_byte(state *S, UWORD addr, BYTE *value)
{
    uint8_t *ptr = native_address(S, addr, false);
    if (ptr == NULL) {
        S->INVALID = addr;
        return -9;
    }
    *value = *ptr;
    return 0;
}

int store_word(state *S, UWORD addr, WORD value)
{
    if (!IS_ALIGNED(addr)) {
        S->INVALID = addr;
        return -23;
    }

    // Aligned access to a single memory allocation
    uint8_t *ptr = native_address_range_in_one_area(S, addr, WORD_SIZE, true);
    if (ptr != NULL && IS_ALIGNED((size_t)ptr)) {
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wcast-align"
        *(WORD *)ptr = value;
#pragma GCC diagnostic pop
        return 0;
    }

    // Awkward access
    int exception = 0;
    for (unsigned i = 0; exception == 0 && i < WORD_SIZE; i++)
        exception = store_byte(S, addr + i, value >> ((S->ENDISM ? WORD_SIZE - i : i) * BYTE_BIT));
    return exception;
}

int store_byte(state *S, UWORD addr, BYTE value)
{
    Mem_area *a = mem_range(S, addr, 1);
    if (a == NULL) {
        S->INVALID = addr;
        return -9;
    } else if (!a->writable) {
        S->INVALID = addr;
        return -20;
    }
    *addr_in_area(a, addr) = value;
    return 0;
}


#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsuggest-attribute=const"
int pre_dma(state *S, UWORD from, UWORD to, bool write)
{
    int exception = 0;

    from &= -WORD_SIZE;
    to = ALIGN(to);
    if (to < from || native_address_range_in_one_area(S, from, to - from, write) == NULL)
        exception = -1;

    return exception;
}
#pragma GCC diagnostic pop

int post_dma(state *S, UWORD from, UWORD to)
{
    return pre_dma(S, from, to, false);
}


state *init(size_t size, size_t data_stack_size, size_t return_stack_size)
{
    WORD *memory = calloc(WORD_SIZE, size);
    if (memory == NULL)
        return NULL;

    state *S = calloc(1, sizeof(state));
    if (S == NULL)
        return NULL;

    S->memory = memory;
    S->MEMORY = size * WORD_SIZE;
    memset(memory, 0, S->MEMORY);

    S->_mem_here = 0UL;

    if ((S->mem_areas =
         gl_list_nx_create_empty(GL_AVLTREE_LIST, eq_mem_area, NULL, free_mem_area, false))
        == NULL)
        return NULL;
    if (mem_allot(S, memory, S->MEMORY, true) == WORD_MASK)
        return NULL;

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
        gl_list_free(S->mem_areas);
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
