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


#define DIVZERO(x)                              \
    if (x == 0)                                 \
        RAISE(-10);

// Defines two macros/functions:
//   void STEP(smite_state *S): runs a single step of the given state.
//   void RAISE(smite_WORD e): raise error e; do nothing if e == 0.

FILE *trace_fp = NULL; // FILE * of trace file, if used
static void trace(int type, smite_WORD opcode) {
    if (trace_fp)
        fprintf(trace_fp, "%d %08x\n", type, (smite_UWORD)opcode);
}

#include "instruction-actions.h"

// Perform one pass of the execution cycle
smite_WORD smite_single_step(smite_state *S)
{
    int error = STEP(S);

    if (error != 0) {
        // Deal with address errors during execution cycle.
        if (error == -255)
            return S->halt_code;
        return error;
    }
    return -258; // terminated OK
}
