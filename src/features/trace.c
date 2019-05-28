// Output instruction trace.
//
// (c) Mit authors 2018-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <unistd.h>
#include <stdio.h>

#include "mit/mit.h"
#include "mit/features.h"


mit_word mit_trace_run(mit_state * restrict state, int trace_fd)
{
    int ret = 0;
    int dup_fd = dup(trace_fd);
    if (dup_fd == -1)
        return -1;
    FILE *fp = fdopen(dup_fd, "wb");
    do {
        uint8_t opcode = (int)(state->I & MIT_OPCODE_MASK);
        putc(opcode, fp);
        ret = mit_single_step(state);
    } while (ret == 0);
    fclose(fp);
    return ret;
}
