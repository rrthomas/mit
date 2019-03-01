// The interface call single_step() : integer.
//
// (c) Reuben Thomas 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdio.h>

#include "smite.h"


FILE *trace_fp = NULL; // FILE * of trace file, if used
static void trace(int type, smite_WORD opcode) {
    if (trace_fp)
        fprintf(trace_fp, "%d %"PRI_XWORD"\n", type, (smite_UWORD)opcode);
}

// Defines the function smite_single_step:
#include "instruction-actions.h"
