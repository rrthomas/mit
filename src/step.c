// The interface call single_step() : integer.
//
// (c) Reuben Thomas 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include "smite.h"


// Defines a function:
//   void do_actions(smite_state *S): runs a single step of the given state.
#define SINGLE_STEPPING
#include "actions.h"

// Perform one pass of the execution cycle
smite_WORD smite_single_step(smite_state *S)
{
    int error = do_actions(S);

    // Normal completion of a single step.
    if (error == 0)
        return -128;

    // Deal with HALT.
    if (error == -127)
        return S->halt_code;

    return error;
}
