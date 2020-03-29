// Macros for the inner loop and instruction actions; see
// mit_core/instruction.py for documentation.
//
// (c) Mit authors 1994-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_RUN
#define MIT_RUN


#include "state.h"


// Arithmetic right shift `n` by `p` places (the behaviour of >> on signed
// quantities is implementation-defined in C99).
#if HAVE_ARITHMETIC_RSHIFT
#define ARSHIFT(n, p) \
    ((mit_word)(n) >> (p))
#else
#define ARSHIFT(n, p) \
    (((n) >> (p)) | ((mit_uword)(-((mit_word)(n) < 0)) << (MIT_WORD_BIT - (p))))
#endif

// Raise an error during the execution of an instruction.
// RAISE must be called before writing any state.
#define RAISE(code)                                           \
    do {                                                      \
        error = (code);                                       \
        goto error;                                           \
    } while (0)

// Check a VM address is valid, raising an error if not.
#define CHECK_ALIGNED(addr)                                   \
    if (!is_aligned((addr), MIT_SIZE_WORD))                   \
        RAISE(MIT_ERROR_UNALIGNED_ADDRESS);

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
static mit_word _fetch_pc(mit_state *S)
{
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wcast-align"
    mit_word w = *(mit_word *)(S->pc);
#pragma GCC diagnostic pop
    S->pc += MIT_WORD_BYTES;
    return w;
}
#pragma GCC diagnostic pop

// Fetch the word at `pc`, assign it to `w`, and increment `pc` by a word.
#define FETCH_PC(w)                                             \
    (w) = (_fetch_pc(S))                                        \

// Perform the action of NEXT.
#define DO_NEXT                                 \
    FETCH_PC(S->ir)

#endif
