// Auto-extend stack and memory on demand.
//
// (c) Mit authors 1994-2019
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

#include "mit/mit.h"
#include "mit/features.h"


#define REGISTER_STRLEN (mit_WORD_BYTES * 2)

static char hex[] = "0123456789abcdef";

static void register_to_str(mit_WORD reg, char s[REGISTER_STRLEN])
{
    for (unsigned i = 0; i < REGISTER_STRLEN; i++) {
        s[REGISTER_STRLEN - i - 1] = hex[reg & 0xf];
        reg >>= 4;
    }
}

int mit_core_dump(mit_state *S)
{
    char pc_str[REGISTER_STRLEN];
    char bad_str[REGISTER_STRLEN];
    register_to_str(S->PC, &pc_str[0]);
    register_to_str(S->BAD, &bad_str[0]);

    // Ignore errors; best effort only, in the middle of an error exit
    char file_format[] = "mit-core.%lu";
    char file[sizeof(file_format) + sizeof(unsigned long) * CHAR_BIT];
    sprintf(file, "mit-core.%lu", (unsigned long)getpid());
    if (file != NULL) {
        int fd;
        if ((fd = creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH)) >= 0) {
            (void)mit_save_object(S, 0, S->memory_size, fd);
            close(fd);
            return 0;

        }
    }
    return -1;
}
