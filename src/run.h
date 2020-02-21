// Macros for the inner loop and instruction actions; see
// mit_core/instruction.py for documentation.
//
// (c) Mit authors 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_RUN
#define MIT_RUN


#include "state.h"


// RAISE(error): the code should RAISE any error before writing any state,
// so that if an error is raised, the state of the VM is not changed.
#define RAISE(code)                                           \
    do {                                                      \
        error = (code);                                       \
        goto error;                                           \
    } while (0)

// CHECK_ALIGNED(addr): check a VM address is valid, raising an error if
// not.
#define CHECK_ALIGNED(addr)                                   \
    if (!is_aligned((addr), MIT_SIZE_WORD))                   \
        RAISE(MIT_ERROR_UNALIGNED_ADDRESS);

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
static mit_word _fetch_pc(mit_state *S)
{
#if MIT_ENDISM == MIT_HOST_ENDISM
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wcast-align"
    mit_word w = *(mit_word *)((uint8_t *)S->memory + S->pc);
#pragma GCC diagnostic pop
#else
    mit_word w = 0;
    load(S->memory, S->memory_bytes, S->pc, MIT_SIZE_WORD, &w);
#endif
    S->pc += MIT_WORD_BYTES;
    return w;
}
#pragma GCC diagnostic pop

// FETCH_PC(w): fetch the word at `pc`, assign it to `w`, and increment `pc`
// by a word.
#define FETCH_PC(w)                                             \
    if (unlikely(S->pc >= S->memory_bytes)) {                   \
        RAISE(MIT_ERROR_INVALID_MEMORY_READ);                   \
    } else {                                                    \
        (w) = (_fetch_pc(S));                                   \
    }

// Perform the action of NEXT.
#define DO_NEXT  FETCH_PC(S->ir)

#endif
