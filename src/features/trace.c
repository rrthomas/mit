// Output instruction trace.
//
// (c) Mit authors 2018-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdio.h>

#include "mit/mit.h"
#include "mit/features.h"


mit_WORD mit_trace_run(mit_state *state, FILE *trace_fp)
{
    int ret = 0;
    do {
        fprintf(trace_fp, "%d\n", (int)(state->I & MIT_INSTRUCTION_MASK));
        ret = mit_single_step(state);
    } while (ret == 0);
    return ret;
}
