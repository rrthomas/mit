// Macros for the inner loop.
//
// (c) Mit authors 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_RUN
#define MIT_RUN


#define RAISE(code)                                           \
    do {                                                      \
        error = (code);                                       \
        goto error;                                           \
    } while (0)

#define FETCH                                                 \
    do {                                                      \
        initial_PC = S->PC;                                   \
        initial_I = S->I;                                     \
        S->I >>= MIT_OPCODE_BIT;                              \
    } while (0)

#define DO_NEXT                                               \
    do {                                                      \
        int ret = load(S->memory, S->memory_size, S->PC,      \
                       MIT_SIZE_WORD, (mit_word *)&(S->I));   \
        if (ret != 0) {                                       \
            S->BAD = S->PC;                                   \
            RAISE(ret);                                       \
        }                                                     \
        S->PC += MIT_WORD_BYTES;                              \
    } while (0)

#endif
