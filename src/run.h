// Macros for the inner loop and instruction actions.
//
// (c) Mit authors 1994-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_RUN
#define MIT_RUN


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
    if (!is_aligned((mit_uword)(addr), MIT_WORD_BYTES))       \
        RAISE(MIT_ERROR_UNALIGNED_ADDRESS);

// Perform the action of NEXT.
#define DO_NEXT                                 \
    S->ir = *S->pc++

#endif
