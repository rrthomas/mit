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

FILE *trace_fp = NULL; // FILE * of trace file, if used
static void trace(int type, smite_WORD opcode) {
    if (trace_fp)
        fprintf(trace_fp, "%d %08x\n", type, (smite_UWORD)opcode);
}

#define DIVZERO(x)                              \
    if (x == 0)                                 \
        RAISE(-10);

static int halt_code;

// Only defined during single_step().
static int exception;

#include "instruction-actions.h"

// Perform one pass of the execution cycle
smite_WORD smite_single_step(smite_state *S)
{
    exception = 0;

    STEP(S);

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
