// Generate a predictor file for the specializer.
//
// (c) Mit authors 2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "mit/mit.h"
#include "mit/features.h"

#include "state.h"


#define HISTORY_BITS 20
#define NUM_HISTORIES (1 << HISTORY_BITS)
#define SPARSITY 3
#define COUNT_THRESHOLD 100



typedef uint32_t history_t;

// Represents a function for updating the history.
struct step_function {
    history_t or_mask;
    history_t xor_mask;
};

// The state of the predictor.
typedef struct {
    struct step_function step_functions[MIT_NUM_OPCODES];
    // For `random_history()`.
    uint64_t seed;
    // How often each opcode has occurred after each history.
    uint64_t counts[NUM_HISTORIES][MIT_NUM_OPCODES];
    // Maps common histories to their index in the output file.
    // Uncommon histories are indicated by `-1`.
    int history_index[NUM_HISTORIES];
    history_t history;
} mit_predictor;

// The (global) predictor.
mit_predictor *predictor;


// Internal to `init_step_functions()`.
// Generate a random HISTORY_BITS-bit number.
static history_t random_history(void) {
    // These odd 64-bit constants come from the digits of pi.
    predictor->seed ^= 0x98EC4E6C89452821ULL;
    predictor->seed *= 0x8A2E03707344A409ULL;
    return predictor->seed >> (64 - HISTORY_BITS);
}

static void init_step_functions(void) {
    for (unsigned opcode = 0; opcode < MIT_NUM_OPCODES; opcode++) {
        predictor->seed = opcode;
        random_history();
        history_t or_mask = (1 << HISTORY_BITS) - 1;
        for (unsigned i = 0; i < SPARSITY; i++)
            or_mask &= random_history();
        predictor->step_functions[opcode].or_mask = or_mask;
        predictor->step_functions[opcode].xor_mask = random_history();
    }
}

static history_t step_function(history_t history, unsigned opcode) {
    struct step_function sf = predictor->step_functions[opcode];
    return (history | sf.or_mask) ^ sf.xor_mask;
}

// Read `counts` and compute `history_index`.
// Returns the number of common histories.
static unsigned index_histories(void) {
    int num_common = 0;
    for (history_t history = 0; history < NUM_HISTORIES; history++) {
        uint64_t total = 0;
        for (unsigned opcode = 0; opcode < MIT_NUM_OPCODES; opcode++)
            total += predictor->counts[history][opcode];
        predictor->history_index[history] = total >= COUNT_THRESHOLD ?
            num_common++ : -1;
    }
    return num_common;
}

// Write a predictor file containing just the histories that are common
// according to `history_index`.
static void write_predictor(FILE *fp) {
    fprintf(fp, "[");
    const char *list_sep = "";
    for (history_t history = 0; history < NUM_HISTORIES; history++) {
        int state = predictor->history_index[history];
        if (state != -1) {
            fprintf(fp, "%s\n    {", list_sep);
            list_sep = ", ";
            const char *dict_sep = "";
            for (unsigned opcode = 0; opcode < MIT_NUM_OPCODES; opcode++) {
                uint64_t count = predictor->counts[history][opcode];
                history_t new_history = step_function(history, opcode);
                int new_state = predictor->history_index[new_history];
                if (count > 0 && new_state != -1) {
                    fprintf(
                        fp,
                        "%s\"%02x\": {\"new_state\": %d, \"count\": %"PRIu64"}",
                        dict_sep, opcode, new_state, count
                    );
                    dict_sep = ", ";
                }
            }
            fprintf(fp, "}");
        }
    }
    fprintf(fp, "\n]");
}


int mit_predictor_init(void)
{
    free(predictor);
    if ((predictor = calloc(1, sizeof(mit_predictor))) == NULL)
        return MIT_MALLOC_ERROR_CANNOT_ALLOCATE_MEMORY;
    init_step_functions();
    predictor->history = 0;
    return MIT_MALLOC_ERROR_OK;
}

int mit_predictor_dump(int fd)
{
    // Open output stream (for buffering)
    int dup_fd = dup(fd);
    if (dup_fd == -1)
        return -1;
    FILE *fp = fdopen(dup_fd, "w");
    if (fp == NULL)
        return -1;

    // Write output
    int num_common_histories = index_histories();
    write_predictor(fp);
    fclose(fp);

    return num_common_histories;
}

mit_word mit_predictor_run(mit_state * restrict state)
{
    int ret = 0;

    // Run, recording history.
    do {
        unsigned opcode = (unsigned)(state->ir & MIT_OPCODE_MASK);
        if (opcode < MIT_NUM_OPCODES) {
            predictor->counts[predictor->history][opcode]++;
            predictor->history = step_function(predictor->history, opcode);
        }
    } while ((ret = mit_single_step(state)) == 0);

    return ret;
}
