// Auto-extend stack and memory on demand.
//
// (c) Mit authors 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <unistd.h>

#include "mit/mit.h"
#include "mit/features.h"


static mit_UWORD page_size;
static mit_UWORD memory_size;
static mit_UWORD stack_size;

static mit_UWORD round_up(mit_UWORD n, mit_UWORD multiple)
{
    return (n - 1) - (n - 1) % multiple + multiple;
}

mit_state *mit_auto_extend_init(void)
{
    // getpagesize() is obsolete, but gnulib provides it, and
    // sysconf(_SC_PAGESIZE) does not work on some platforms.
    page_size = getpagesize();
    memory_size = WORD_BYTES == 2 ? 0x1000U : 0x100000U;
    stack_size = WORD_BYTES == 2 ? 1024U : 16384U;

    return mit_init(memory_size, stack_size);
}

int mit_auto_extend_handler(mit_state *S, int error)
{
    switch (error) {
    case 2:
        // Grow stack on demand
        if (S->BAD >= S->stack_size &&
            S->BAD < mit_uword_max - S->stack_size &&
            mit_realloc_stack(S, round_up(S->stack_size + S->BAD, page_size)) == 0)
            return 0;
        break;
    case 5:
    case 6:
        // Grow memory on demand
        if (S->BAD >= S->memory_size &&
            mit_realloc_memory(S, round_up(S->BAD, page_size)) == 0)
            return 0;
        break;
    default:
        break;
    }

    return error;
}
