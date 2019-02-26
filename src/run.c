// The interface call run() : integer.
//
// (c) Reuben Thomas 1994-2016
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "smite.h"


#include "actions.h"

smite_WORD smite_run(smite_state *S)
{
    int error;
    while ((error = do_actions(S)) == 0)
        ;

    // Deal with HALT.
    if (error == -127)
        return S->halt_code;

    return error;
}
