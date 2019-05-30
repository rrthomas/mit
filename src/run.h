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

#define CHECK_ALIGNED(addr)                                   \
    if (!is_aligned((addr), MIT_SIZE_WORD)) {                 \
        S->BAD = (addr);                                      \
        RAISE(MIT_ERROR_UNALIGNED_ADDRESS);                   \
    }

#define CHECK_ADDRESS(addr)                                   \
        if (unlikely((addr) >= S->memory_size - MIT_WORD_BYTES)) { \
            S->BAD = (addr);                                  \
            RAISE(MIT_ERROR_INVALID_MEMORY_READ);             \
        }                                                     \

#if MIT_ENDISM == MIT_HOST_ENDISM
#define LOAD_WORD(w, addr)                                    \
    do {                                                      \
        CHECK_ADDRESS(addr);                                  \
        (w) = *(mit_word *)((uint8_t *)S->memory + (addr));   \
    } while (0)
#else
#define LOAD_WORD(w, addr)                                              \
    do {                                                                \
        CHECK_ADDRESS(addr);                                            \
        mit_word p = 0;                                                 \
        load(S->memory, S->memory_size, (addr), MIT_SIZE_WORD, &p);     \
        (w) = p;                                                        \
    } while (0)
#endif

#define DO_NEXT                                               \
    do {                                                      \
        LOAD_WORD(S->I, S->PC);                               \
        S->PC += MIT_WORD_BYTES;                              \
    } while (0)

#endif
