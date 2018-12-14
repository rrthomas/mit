// The interface call single_step() : integer.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "external_syms.h"

#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include "binary-io.h"
#include "verify.h"

#include "public.h"
#include "aux.h"
#include "private.h"
#include "opcodes.h"


// Assumption for file functions
verify(sizeof(int) <= sizeof(WORD));


// Check whether a VM address points to a native word-aligned word
#define WORD_IN_ONE_AREA(a)                             \
    (native_address_range_in_one_area((a), WORD_SIZE, false) != NULL)

#define DIVZERO(x)                              \
    if (x == 0)                                 \
        exception = -10;


// I/O support

// Copy a string from VM to native memory
static int getstr(UWORD adr, UWORD len, char **res)
{
    int exception = 0;

    *res = calloc(1, len + 1);
    if (*res == NULL)
        exception = -511;
    else
        for (size_t i = 0; exception == 0 && i < len; i++, adr++) {
            exception = load_byte(adr, (BYTE *)((*res) + i));
        }

    return exception;
}

// Convert portable open(2) flags bits to system flags
static int getflags(UWORD perm, bool *binary)
{
    int flags = 0;

    switch (perm & 3) {
    case 0:
        flags = O_RDONLY;
        break;
    case 1:
        flags = O_WRONLY;
        break;
    case 2:
        flags = O_RDWR;
        break;
    default:
        break;
    }
    if (perm & 4)
        flags |= O_CREAT | O_TRUNC;

    if (perm & 8)
        *binary = true;

    return flags;
}

// Register command-line args in VM memory
static int main_argc = 0;
static UWORD *main_argv;
static UWORD *main_argv_len;
int register_args(int argc, char *argv[])
{
    main_argc = argc;
    if ((main_argv = calloc(argc, sizeof(UWORD))) == NULL ||
        (main_argv_len = calloc(argc, sizeof(UWORD))) == NULL)
        return -1;

    for (int i = 0; i < argc; i++) {
        size_t len = strlen(argv[i]);
        main_argv[i] = mem_allot(argv[i], len, true);
        if (main_argv[i] == 0)
            return -2;
        main_argv_len[i] = len;
    }
    return 0;
}

static void extra(void)
{
    int exception = 0;
    WORD temp = 0;
#if WORD_SIZE == 4
    WORD temp2 = 0;
#endif
    switch (POP) {
    case OX_ARGC: // ( -- u )
        PUSH(main_argc);
        break;
    case OX_ARG: // ( u1 -- c-addr u2 )
        {
            UWORD narg = POP;
            if (narg >= (UWORD)main_argc) {
                PUSH(0);
                PUSH(0);
            } else {
                PUSH(main_argv[narg]);
                PUSH(main_argv_len[narg]);
            }
        }
        break;
    case OX_STDIN:
        PUSH((WORD)(STDIN_FILENO));
        break;
    case OX_STDOUT:
        PUSH((WORD)(STDOUT_FILENO));
        break;
    case OX_STDERR:
        PUSH((WORD)(STDERR_FILENO));
        break;
    case OX_OPEN_FILE:
        {
            bool binary = false;
            int perm = getflags(POP, &binary);
            UWORD len = POP;
            UWORD str = POP;
            char *file;
            exception = getstr(str, len, &file);
            int fd = exception == 0 ? open(file, perm, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            free(file);
            PUSH((WORD)fd);
            PUSH(fd < 0 || (binary && set_binary_mode(fd, O_BINARY) < 0) ? -1 : 0);
        }
        break;
    case OX_CLOSE_FILE:
        {
            int fd = POP;
            PUSH((WORD)close(fd));
        }
        break;
    case OX_READ_FILE:
        {
            int fd = POP;
            UWORD nbytes = POP;
            UWORD buf = POP;

            ssize_t res = 0;
            if (exception == 0) {
                exception = pre_dma(buf, buf + nbytes, true);
                if (exception == 0) {
                    res = read(fd, native_address(buf, true), nbytes);
                    exception = post_dma(buf, buf + nbytes);
                }
            }

            PUSH(res);
            PUSH((exception == 0 && res >= 0) ? 0 : -1);
        }
        break;
    case OX_WRITE_FILE:
        {
            int fd = POP;
            UWORD nbytes = POP;
            UWORD buf = POP;

            ssize_t res = 0;
            if (exception == 0) {
                exception = pre_dma(buf, buf + nbytes, false);
                if (exception == 0) {
                    res = write(fd, native_address(buf, false), nbytes);
                    exception = post_dma(buf, buf + nbytes);
                }
            }

            PUSH((exception == 0 && res >= 0) ? 0 : -1);
        }
        break;
    case OX_FILE_POSITION:
        {
            int fd = POP;
            off_t res = lseek(fd, 0, SEEK_CUR);
            PUSH64((uint64_t)res);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case OX_REPOSITION_FILE:
        {
            int fd = POP;
            uint64_t ud = POP64;
            off_t res = lseek(fd, (off_t)ud, SEEK_SET);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case OX_FLUSH_FILE:
        {
            int fd = POP;
            int res = fdatasync(fd);
            PUSH(res);
        }
        break;
    case OX_RENAME_FILE:
        {
            UWORD len1 = POP;
            UWORD str1 = POP;
            UWORD len2 = POP;
            UWORD str2 = POP;
            char *from;
            char *to = NULL;
            exception = getstr(str2, len2, &from) ||
                getstr(str1, len1, &to) ||
                rename(from, to);
            free(from);
            free(to);
            PUSH(exception);
        }
        break;
    case OX_DELETE_FILE:
        {
            UWORD len = POP;
            UWORD str = POP;
            char *file;
            exception = getstr(str, len, &file) ||
                remove(file);
            free(file);
            PUSH(exception);
        }
        break;
    case OX_FILE_SIZE:
        {
            struct stat st;
            int fd = POP;
            int res = fstat(fd, &st);
            PUSH64(st.st_size);
            PUSH(res);
        }
        break;
    case OX_RESIZE_FILE:
        {
            int fd = POP;
            uint64_t ud = POP64;
            int res = ftruncate(fd, (off_t)ud);
            PUSH(res);
        }
        break;
    case OX_FILE_STATUS:
        {
            struct stat st;
            int fd = POP;
            int res = fstat(fd, &st);
            PUSH(st.st_mode);
            PUSH(res);
        }
        break;
    }
}


// Perform one pass of the execution cycle
WORD single_step(void)
{
    int exception = 0;
    WORD temp = 0;
    BYTE byte = 0;

    int type = decode_instruction(&PC, &I);
    switch (type) {
    case INSTRUCTION_NUMBER:
        PUSH(I);
        break;
    case INSTRUCTION_ACTION:
        switch (I) {
#include "instruction-actions.h"

        default: // Undefined instruction
            exception = -256;
            break;
        }
        break;
    default: // Exception during instruction fetch
        exception = type;
        break;
    }

    if (exception != 0) {
        // Deal with address exceptions during execution cycle.
        // Since we have already had an exception, and must return a different
        // code from usual if SP is now invalid, push the exception code
        // "manually".
        SP += WORD_SIZE * STACK_DIRECTION;
        if (!WORD_IN_ONE_AREA(SP) || !IS_ALIGNED(SP))
            return -257;
        int store_exception = store_word(SP, exception);
        assert(store_exception == 0);
        BADPC = PC - 1;
        PC = HANDLER;
    }
    return -259; // terminated OK
}
