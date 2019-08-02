// Running a number of instructions or to a particular address, in C for speed.
//
// (c) Mit authors 2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include "mit/mit.h"
#include "mit/features.h"


// Single-step for n steps (excluding NEXT when pc does not change), or
// until pc=addr.
mit_word mit_step_to(mit_state * restrict state, mit_uword *n_ptr, mit_uword addr, int auto_NEXT)
{
    mit_word error = 0;
    mit_uword n = *n_ptr, done;
    for (done = 0;
         error == 0 && ((n == 0 && state->pc != addr) || done < n);
         done++) {
        if (auto_NEXT && state->ir == 0)
            done--;
        error = mit_single_step(state);
        if (error == 1 && (state->ir & MIT_OPCODE_MASK) == MIT_INSTRUCTION_JUMP) {
            error = mit_extra_instruction(state);
            state->ir = 0; // Skip to next instruction
        }
    }
    *n_ptr = done;
    return error;
}
