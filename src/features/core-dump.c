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

#include "binary-io.h"

#include "mit/mit.h"
#include "mit/features.h"

#include "state.h"


const char *mit_core_dump(mit_state *S)
{
    // Ignore errors; best effort only, in the middle of an error exit
    char file_format[] = "mit-core.%lu";
    static char file[sizeof(file_format) + sizeof(unsigned long) * CHAR_BIT];
    sprintf(file, "mit-core.%lu", (unsigned long)getpid());
    int fd = creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
    set_binary_mode (fd, O_BINARY); // Best effort
    if (fd >= 0) {
        (void)mit_save_object(S, 0, S->memory_bytes, fd);
        close(fd);
        return file;
    }
    return NULL;
}
