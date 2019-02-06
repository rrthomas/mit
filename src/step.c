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


#include "instruction-actions.h"
// Defines two macros/functions:
//   void STEP(smite_state *S): runs a single step of the given state.
//   void RAISE(smite_WORD e): raise error e; do nothing if e == 0.

// Perform one pass of the execution cycle
smite_WORD smite_single_step(smite_state *S)
{
    S->exception = 0;

    STEP(S);

    if (S->exception != 0) {
        // Deal with address exceptions during execution cycle.
        if (S->exception == -255)
            return S->halt_code;
        return S->exception;
    }
    return -258; // terminated OK
}
