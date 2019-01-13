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

#include "external-syms.h"

#include <assert.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include "binary-io.h"
#include "verify.h"
#include "minmax.h"

#include "public.h"
#include "aux.h"
#include "opcodes.h"


// Assumption for file functions
verify(sizeof(int) <= sizeof(WORD));


#define DIVZERO(x)                              \
    if (x == 0)                                 \
        exception = -10;


// I/O support

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

// Register command-line args
int register_args(state *S, int argc, char *argv[])
{
    S->main_argc = argc;
    S->main_argv = argv;

    if ((S->main_argv_len = calloc(argc, sizeof(UWORD))) == NULL)
        return -1;
    for (int i = 0; i < argc; i++)
        S->main_argv_len[i] = strlen(argv[i]);

    return 0;
}

static int extra_smite(state *S)
{
    int exception = 0;

    UWORD routine;
    POP((WORD *)&routine);
    switch (routine) {
    case OX_SMITE_CURRENT_STATE:
        PUSH_NATIVE_TYPE(state *, S);
        break;
    case OX_SMITE_LOAD_WORD:
        {
            UWORD addr;
            POP((WORD *)&addr);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            WORD value;
            int ret = load_word(inner_state, addr, &value);
            PUSH(value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_STORE_WORD:
        {
            WORD value;
            POP(&value);
            UWORD addr;
            POP((WORD *)&addr);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            int ret = store_word(inner_state, addr, value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_LOAD_BYTE:
        {
            UWORD addr;
            POP((WORD *)&addr);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            BYTE value;
            int ret = load_byte(inner_state, addr, &value);
            PUSH(value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_STORE_BYTE:
        {
            WORD value;
            POP(&value);
            UWORD addr;
            POP((WORD *)&addr);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            int ret = store_byte(inner_state, addr, (BYTE)value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_MEM_REALLOC:
        {
            UWORD n;
            POP((WORD *)&n);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            UWORD ret = mem_realloc(inner_state, (size_t)n);
            PUSH(ret);
        }
        break;
    case OX_SMITE_NATIVE_ADDRESS_OF_RANGE:
        {
            UWORD len;
            POP((WORD *)&len);
            UWORD addr;
            POP((WORD *)&addr);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            uint8_t *ptr = native_address_of_range(inner_state, addr, len);
            PUSH_NATIVE_TYPE(uint8_t *, ptr);
        }
        break;
    case OX_SMITE_RUN:
        {
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            int ret = run(inner_state);
            PUSH(ret);
        }
        break;
    case OX_SMITE_SINGLE_STEP:
        {
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            int ret = single_step(inner_state);
            PUSH(ret);
        }
        break;
    case OX_SMITE_LOAD_OBJECT:
        {
            UWORD address;
            POP((WORD *)&address);
            WORD fd;
            POP(&fd);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            int ret = load_object(inner_state, (int)fd, address);
            PUSH(ret);
        }
        break;
    case OX_SMITE_INIT:
        {
            UWORD return_stack_size;
            POP((WORD *)&return_stack_size);
            UWORD stack_size;
            POP((WORD *)&stack_size);
            UWORD memory_size;
            POP((WORD *)&memory_size);
            state *new_state = init((size_t)memory_size, (size_t)stack_size, (size_t)return_stack_size);
            PUSH_NATIVE_TYPE(state *, new_state);
        }
        break;
    case OX_SMITE_DESTROY:
        {
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            destroy(inner_state);
        }
        break;
    case OX_SMITE_REGISTER_ARGS:
        {
            char **argv;
            POP_NATIVE_TYPE(char **, &argv);
            WORD argc;
            POP(&argc);
            state *inner_state;
            POP_NATIVE_TYPE(state *, &inner_state);
            int ret = register_args(inner_state, (int)argc, argv);
            PUSH(ret);
        }
        break;
    default:
        exception = -260;
        break;
    }

    return exception;
}

static int extra_libc(state *S)
{
    int exception = 0;

    UWORD routine;
    POP((WORD *)&routine);
    switch (routine) {
    case OX_ARGC: // ( -- u )
        PUSH(S->main_argc);
        break;
    case OX_ARG_LEN: // ( u1 -- u2 )
        {
            UWORD narg;
            POP((WORD *)&narg);
            if (narg >= (UWORD)S->main_argc)
                PUSH(0);
            else
                PUSH(S->main_argv_len[narg]);
        }
        break;
    case OX_ARG_COPY: // ( u1 c-addr u2 -- u3 )
        {
            UWORD len;
            POP((WORD *)&len);
            UWORD buf;
            POP((WORD *)&buf);
            UWORD narg;
            POP((WORD *)&narg);

            if (exception == 0 && narg < (UWORD)S->main_argc) {
                len = MIN(len, S->main_argv_len[narg]);
                uint8_t *ptr = native_address_of_range(S, buf, len);
                if (ptr) {
                    memcpy(ptr, S->main_argv[narg], len);
                    PUSH(len);
                } else
                    PUSH(0);
            } else
                PUSH(0);
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
            WORD perm_;
            POP(&perm_);
            int perm = getflags(perm_, &binary);
            UWORD len;
            POP((WORD *)&len);
            UWORD str;
            POP((WORD *)&str);
            char *s = (char *)native_address_of_range(S, str, len);
            int fd = s ? open(s, perm, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            PUSH((WORD)fd);
            PUSH(fd < 0 || (binary && set_binary_mode(fd, O_BINARY) < 0) ? -1 : 0);
        }
        break;
    case OX_CLOSE_FILE:
        {
            WORD fd;
            POP(&fd);
            PUSH((WORD)close(fd));
        }
        break;
    case OX_READ_FILE:
        {
            WORD fd;
            POP(&fd);
            UWORD nbytes;
            POP((WORD *)&nbytes);
            UWORD buf;
            POP((WORD *)&buf);

            ssize_t nread = 0;
            if (exception == 0) {
                uint8_t *ptr = native_address_of_range(S, buf, nbytes);
                if (ptr)
                    nread = read((int)fd, ptr, nbytes);
            }

            PUSH(nread);
            PUSH((exception == 0 && nread >= 0) ? 0 : -1);
        }
        break;
    case OX_WRITE_FILE:
        {
            WORD fd;
            POP(&fd);
            UWORD nbytes;
            POP((WORD *)&nbytes);
            UWORD buf;
            POP((WORD *)&buf);

            ssize_t nwritten = 0;
            if (exception == 0) {
                uint8_t *ptr = native_address_of_range(S, buf, nbytes);
                if (ptr)
                    nwritten = write((int)fd, ptr, nbytes);
            }

            // FIXME: push number of bytes written, symmetric with READ_FILE
            PUSH((exception == 0 && nwritten >= 0) ? 0 : -1);
        }
        break;
    case OX_FILE_POSITION:
        {
            WORD fd;
            POP(&fd);
            off_t res = lseek((int)fd, 0, SEEK_CUR);
            PUSH_NATIVE_TYPE(off_t, res);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case OX_REPOSITION_FILE:
        {
            WORD fd;
            POP(&fd);
            off_t off;
            POP_NATIVE_TYPE(off_t, &off);
            off_t res = lseek((int)fd, off, SEEK_SET);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case OX_FLUSH_FILE:
        {
            WORD fd;
            POP(&fd);
            int res = fdatasync((int)fd);
            PUSH(res);
        }
        break;
    case OX_RENAME_FILE:
        {
            UWORD len1;
            POP((WORD *)&len1);
            UWORD str1;
            POP((WORD *)&str1);
            UWORD len2;
            POP((WORD *)&len2);
            UWORD str2;
            POP((WORD *)&str2);
            char *s1 = (char *)native_address_of_range(S, str1, len1);
            char *s2 = (char *)native_address_of_range(S, str2, len2);
            exception = (s1 == NULL || s2 == NULL) ? -9 : rename(s2, s1);
            PUSH(exception);
        }
        break;
    case OX_DELETE_FILE:
        {
            UWORD len;
            POP((WORD *)&len);
            UWORD str;
            POP((WORD *)&str);
            char *s = (char *)native_address_of_range(S, str, len);
            exception = s == NULL ? -9 : remove(s);
            PUSH(exception);
        }
        break;
    case OX_FILE_SIZE:
        {
            struct stat st;
            WORD fd;
            POP(&fd);
            int res = fstat((int)fd, &st);
            PUSH_NATIVE_TYPE(off_t, st.st_size);
            PUSH(res);
        }
        break;
    case OX_RESIZE_FILE:
        {
            WORD fd;
            POP(&fd);
            off_t off;
            POP_NATIVE_TYPE(off_t, &off);
            int res = ftruncate((int)fd, off);
            PUSH(res);
        }
        break;
    case OX_FILE_STATUS:
        {
            struct stat st;
            WORD fd;
            POP(&fd);
            int res = fstat((int)fd, &st);
            PUSH(st.st_mode);
            PUSH(res);
        }
        break;
    default:
        exception = -260;
        break;
    }

    return exception;
}

static int extra(state *S)
{
    int exception = 0;

    UWORD lib;
    POP((WORD *)&lib);
    switch (lib) {
    case OXLIB_SMITE:
        exception = extra_smite(S);
        break;
    case OXLIB_LIBC:
        exception = extra_libc(S);
        break;
    default:
        exception = -259;
        break;
    }

    return exception;
}


// Perform one pass of the execution cycle
WORD single_step(state *S)
{
    int exception = 0;

    S->ITYPE = decode_instruction(S, &S->PC, &S->I);
    switch (S->ITYPE) {
    case INSTRUCTION_NUMBER:
        PUSH(S->I);
        break;
    case INSTRUCTION_ACTION:
        switch (S->I) {
#include "instruction-actions.h"

        default: // Undefined instruction
            exception = -256;
            break;
        }
        break;
    default: // Exception during instruction fetch
        exception = S->ITYPE;
        break;
    }

    if (exception != 0) {
        // Deal with address exceptions during execution cycle.
        S->BADPC = S->PC - 1;
        if (push_stack(S->S0, S->SSIZE, &(S->SDEPTH), exception) != 0)
            return -257;
        exception = 0;
        S->PC = S->HANDLER;
    }
    return -258; // terminated OK
}
