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
#include "private.h"


// VM registers

UWORD PC;
WORD I;
UWORD SP, RP;
UWORD HASHS = DEFAULT_STACK_SIZE;
UWORD S0, R0;
UWORD HASHR = DEFAULT_STACK_SIZE;
UWORD HANDLER;
UWORD MEMORY;
UWORD BADPC;
UWORD INVALID;


// Memory allocation and mapping
static gl_list_t mem_areas;
static UWORD _mem_here;

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

_GL_ATTRIBUTE_PURE UWORD mem_here(void)
{
    return _mem_here;
}

// Given a range of addresses, return Mem_area corresponding to some address
// in that range.
// This is used a) to find the area for a particular word;
//              b) to test whether part of a range has already been allocated
static Mem_area *mem_range(UWORD start, UWORD length)
{
    Mem_area a_addr = {start, length, NULL, true};
    gl_list_node_t elt = gl_sortedlist_search(mem_areas, cmp_mem_area, &a_addr);
    return elt ? (Mem_area *)gl_list_node_value(mem_areas, elt) : NULL;
}

#define addr_in_area(a, addr) (a->ptr + ((addr) - a->start))

_GL_ATTRIBUTE_PURE uint8_t *native_address(UWORD addr, bool write)
{
    Mem_area *a = mem_range(addr, 1);
    if (a == NULL || (write && !a->writable))
        return NULL;
    return addr_in_area(a, addr);
}

// Return address of a range iff it falls inside an area
uint8_t *native_address_range_in_one_area(UWORD start, UWORD length, bool write)
{
    Mem_area *a = mem_range(start, 1);
    if (a == NULL || (write && !a->writable) || a->size - (start - a->start) < length)
        return NULL;
    return addr_in_area(a, start);
}

// Map the given native block of memory to VM address addr
static bool mem_map(UWORD addr, void *p, size_t n, bool writable)
{
    // Return false if area is too big, or covers already-allocated addresses
    if ((addr > 0 && n > (WORD_MAX - addr + 1)) || mem_range(addr, n) != NULL)
        return false;

    Mem_area *area = malloc(sizeof(Mem_area));
    if (area == NULL)
        return false;
    *area = (Mem_area){addr, n, p, writable};

    gl_list_node_t elt = gl_sortedlist_nx_add(mem_areas, cmp_mem_area, area);
    if (elt == NULL)
        return false;

    return true;
}

UWORD mem_allot(void *p, size_t n, bool writable)
{
    if (!mem_map(_mem_here, p, n, writable))
        return WORD_MASK;

    size_t start = _mem_here;
    _mem_here += n;
    return start;
}

UWORD mem_align(void)
{
    return _mem_here = ALIGN(_mem_here);
}


// General memory access

// Macro for byte addressing
#ifdef WORDS_BIGENDIAN
#define FLIP(addr) ((addr) ^ (WORD_SIZE - 1))
#else
#define FLIP(addr) (addr)
#endif

int load_word(UWORD addr, WORD *value)
{
    if (!IS_ALIGNED(addr)) {
        INVALID = addr;
        return -23;
    }

    // Aligned access to a single memory area
    uint8_t *ptr = native_address_range_in_one_area(addr, WORD_SIZE, false);
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
        ptr = native_address(addr, false);
        if (ptr == NULL) {
            INVALID = addr;
            return -9;
        }
        ((BYTE *)value)[ENDISM ? WORD_SIZE - i : i] = *ptr;
    }
    return 0;
}

int load_byte(UWORD addr, BYTE *value)
{
    uint8_t *ptr = native_address(FLIP(addr), false);
    if (ptr == NULL) {
        INVALID = addr;
        return -9;
    }
    *value = *ptr;
    return 0;
}

int store_word(UWORD addr, WORD value)
{
    if (!IS_ALIGNED(addr)) {
        INVALID = addr;
        return -23;
    }

    // Aligned access to a single memory allocation
    uint8_t *ptr = native_address_range_in_one_area(addr, WORD_SIZE, true);
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
        exception = store_byte(addr + i, value >> ((ENDISM ? WORD_SIZE - i : i) * BYTE_BIT));
    return exception;
}

int store_byte(UWORD addr, BYTE value)
{
    Mem_area *a = mem_range(FLIP(addr), 1);
    if (a == NULL) {
        INVALID = addr;
        return -9;
    } else if (!a->writable) {
        INVALID = addr;
        return -20;
    }
    *addr_in_area(a, FLIP(addr)) = value;
    return 0;
}


_GL_ATTRIBUTE_CONST WORD reverse_word(WORD value)
{
    WORD res = 0;
    for (unsigned i = 0; i < WORD_SIZE / 2; i++) {
        unsigned lopos = BYTE_BIT * i;
        unsigned hipos = BYTE_BIT * (WORD_SIZE - 1 - i);
        unsigned move = hipos - lopos;
        res |= ((((UWORD)value) & ((UWORD)BYTE_MASK << hipos)) >> move)
            | ((((UWORD)value) & ((UWORD)BYTE_MASK << lopos)) << move);
    }
    return res;
}

int reverse(UWORD start, UWORD length)
{
    int ret = 0;
    for (UWORD i = 0; ret == 0 && i < length; i ++) {
        WORD c;
        ret = load_word(start + i * WORD_SIZE, &c)
            || store_word(start + i, reverse_word(c));
    }
    return ret;
}

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsuggest-attribute=const"
int pre_dma(UWORD from, UWORD to, bool write)
{
    int exception = 0;

    from &= -WORD_SIZE;
    to = ALIGN(to);
    if (to < from || native_address_range_in_one_area(from, to - from, write) == NULL)
        exception = -1;
    CHECK_ALIGNED(from);
    CHECK_ALIGNED(to);
    if (exception == 0 && ENDISM)
        exception = reverse(from, to - from);

    return exception;
}
#pragma GCC diagnostic pop

int post_dma(UWORD from, UWORD to)
{
    return pre_dma(from, to, false);
}


// Initialise registers that are not fixed

int init(WORD *memory, size_t size)
{
    if (memory == NULL)
        return -1;
    MEMORY = size * WORD_SIZE;
    memset(memory, 0, MEMORY);

    _mem_here = 0UL;

    if (mem_areas)
        gl_list_free(mem_areas);
    if ((mem_areas =
         gl_list_nx_create_empty(GL_AVLTREE_LIST, eq_mem_area, NULL, free_mem_area, false))
        == false)
        return -2;

    if (mem_allot(memory, MEMORY, true) == WORD_MASK)
        return -2;

    WORD *d_stack = calloc(HASHS, WORD_SIZE);
    WORD *r_stack = calloc(HASHR, WORD_SIZE);
    if (d_stack == NULL || r_stack == NULL)
        return -2;

    if (!mem_map(DATA_STACK_SEGMENT, d_stack, HASHS, true)
        || !mem_map(RETURN_STACK_SEGMENT, r_stack, HASHR, true))
        return -2;

    PC = 0;
    I = 0;
    S0 = SP = DATA_STACK_SEGMENT;
    R0 = RP = RETURN_STACK_SEGMENT;
    HANDLER = 0;
    BADPC = 0;
    INVALID = 0;

    return 0;
}
