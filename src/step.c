// The interface call single_step() : integer.
//
// (c) Reuben Thomas 1994-2019
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include <assert.h>
#include "verify.h"

#include "smite.h"
#include "aux.h"
#include "opcodes.h"
#include "extra.h"


// Assumption for file functions
verify(sizeof(int) <= sizeof(smite_WORD));


#ifndef RAISE
#define RAISE(code)                             \
        exception = (code);
#endif

#define DIVZERO(x)                              \
    if (x == 0)                                 \
        RAISE(-10);


static int halt_code;

// Only defined during single_step().
static int exception;

// Perform one pass of the execution cycle
smite_WORD smite_single_step(smite_state *S)
{
    exception = 0;

    S->ITYPE = smite_decode_instruction(S, &S->PC, &S->I);
    switch (S->ITYPE) {
    case INSTRUCTION_NUMBER:
        PUSH(S->I);
        break;
    case INSTRUCTION_ACTION:
        switch (S->I) {
#include "instruction-actions.h"

        default: // Undefined instruction
            exception = -256;
            break;
        }
        break;
    default: // Exception during instruction fetch
        exception = S->ITYPE;
        break;
    }

    if (exception != 0) {
        // Deal with address exceptions during execution cycle.
        if (exception == -255)
            return halt_code;
        S->BADPC = S->PC - 1;
        if (smite_push_stack(S, exception) != 0)
            return -257;
        exception = 0;
        S->PC = S->HANDLER;
    }
    return -258; // terminated OK
}
