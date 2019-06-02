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


#define RAISE(code)                                           \
    do {                                                      \
        error = (code);                                       \
        goto error;                                           \
    } while (0)

#define CHECK_ALIGNED(addr)                                   \
    if (!is_aligned((addr), MIT_SIZE_WORD)) {                 \
        S->BAD = (addr);                                      \
        RAISE(MIT_ERROR_UNALIGNED_ADDRESS);                   \
    }

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
static mit_word _fetch_pc(mit_state *S)
{
#if MIT_ENDISM == MIT_HOST_ENDISM
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wcast-align"
    mit_word w = *(mit_word *)((uint8_t *)S->memory + S->PC);
#pragma GCC diagnostic pop
#else
    mit_word w = 0;
    load(S->memory, S->memory_size, S->PC, MIT_SIZE_WORD, &w);
#endif
    S->PC += MIT_WORD_BYTES;
    return w;
}
#pragma GCC diagnostic pop

#define FETCH_PC(w)                                             \
    if (unlikely(S->PC >= S->memory_size - MIT_WORD_BYTES)) {   \
        S->BAD = S->PC;                                         \
        RAISE(MIT_ERROR_INVALID_MEMORY_READ);                   \
    } else {                                                    \
        (w) = (_fetch_pc(S));                                   \
    }

#define DO_NEXT  FETCH_PC(S->I)

#endif
