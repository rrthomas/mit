// Auto-extend stack and memory on demand.
//
// (c) Mit authors 1994-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

#include "binary-io.h"

#include "mit/mit.h"
#include "mit/features.h"

#include "state.h"


const char *mit_core_dump(mit_word *addr, mit_uword words)
{
    // Ignore errors; best effort only, in the middle of an error exit
    char file_format[] = "mit-core.%lu";
    static char file[sizeof(file_format) + sizeof(unsigned long) * CHAR_BIT];
    sprintf(file, "mit-core.%lu", (unsigned long)getpid());
    FILE *fp = fopen(file, "wb");
    if (fp != NULL) {
        (void)fwrite(addr, sizeof(mit_word), words, fp);
        (void)fclose(fp);
        return file;
    }
    return NULL;
}
