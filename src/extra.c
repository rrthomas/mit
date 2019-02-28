// EXTRA instruction support.
//
// (c) Reuben Thomas 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

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

#include "smite.h"
#include "aux.h"
#include "extra.h"
#include "opcodes.h"


// Assumption for file functions
verify(sizeof(int) <= sizeof(smite_WORD));


// RAISE(code) must be define before using `PUSH` or `POP`.
// It must somehow exit if `code` is non-zero, e.g. return `code` to caller.

#define POP(v)                                                          \
    RAISE(smite_pop_stack(S, v))
#define PUSH(v)                                                         \
    RAISE(smite_push_stack(S, v))

#define PUSH_NATIVE_TYPE(ty, v)                                         \
    for (unsigned i = 0; i < smite_align(sizeof(ty)) / smite_word_size; i++) { \
        PUSH((smite_UWORD)((size_t)v & smite_word_mask));               \
        v = (ty)((size_t)v >> smite_word_bit);                          \
    }
#define POP_NATIVE_TYPE(ty, v)                                          \
    *v = 0;                                                             \
    for (unsigned i = 0; i < smite_align(sizeof(ty)) / smite_word_size; i++) { \
        smite_WORD w;                                                   \
        POP(&w);                                                        \
        *v = (ty)(((size_t)(*v) << smite_word_bit) | (smite_UWORD)w);   \
    }


// I/O support

// Convert portable open(2) flags bits to system flags
static int getflags(smite_UWORD perm, bool *binary)
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
int smite_register_args(smite_state *S, int argc, char *argv[])
{
    S->main_argc = argc;
    S->main_argv = argv;

    if ((S->main_argv_len = calloc(argc, sizeof(smite_UWORD))) == NULL)
        return -1;
    for (int i = 0; i < argc; i++)
        S->main_argv_len[i] = strlen(argv[i]);

    return 0;
}

#define RAISE(error)                                                    \
    do {                                                                \
        if (error != 0)                                                 \
            return error;                                               \
    } while(0)

static int extra_smite(smite_state *S)
{
    smite_UWORD routine;
    POP((smite_WORD *)&routine);
    switch (routine) {
    case LIB_SMITE_CURRENT_STATE:
        PUSH_NATIVE_TYPE(smite_state *, S);
        break;
    case LIB_SMITE_LOAD_WORD:
        {
            smite_UWORD addr;
            POP((smite_WORD *)&addr);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            smite_WORD value;
            int ret = smite_load_word(inner_smite_state, addr, &value);
            PUSH(value);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_STORE_WORD:
        {
            smite_WORD value;
            POP(&value);
            smite_UWORD addr;
            POP((smite_WORD *)&addr);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            int ret = smite_store_word(inner_smite_state, addr, value);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_LOAD_BYTE:
        {
            smite_UWORD addr;
            POP((smite_WORD *)&addr);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            smite_BYTE value;
            int ret = smite_load_byte(inner_smite_state, addr, &value);
            PUSH(value);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_STORE_BYTE:
        {
            smite_WORD value;
            POP(&value);
            smite_UWORD addr;
            POP((smite_WORD *)&addr);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            int ret = smite_store_byte(inner_smite_state, addr, (smite_BYTE)value);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_REALLOC_MEMORY:
        {
            smite_UWORD n;
            POP((smite_WORD *)&n);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            smite_UWORD ret = smite_realloc_memory(inner_smite_state, (size_t)n);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_REALLOC_STACK:
        {
            smite_UWORD n;
            POP((smite_WORD *)&n);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            smite_UWORD ret = smite_realloc_stack(inner_smite_state, (size_t)n);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_NATIVE_ADDRESS_OF_RANGE:
        {
            smite_UWORD len;
            POP((smite_WORD *)&len);
            smite_UWORD addr;
            POP((smite_WORD *)&addr);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            uint8_t *ptr = smite_native_address_of_range(inner_smite_state, addr, len);
            PUSH_NATIVE_TYPE(uint8_t *, ptr);
        }
        break;
    case LIB_SMITE_RUN:
        {
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            int ret = smite_run(inner_smite_state);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_SINGLE_STEP:
        {
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            int ret = smite_single_step(inner_smite_state);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_LOAD_OBJECT:
        {
            smite_UWORD address;
            POP((smite_WORD *)&address);
            smite_WORD fd;
            POP(&fd);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            int ret = smite_load_object(inner_smite_state, (int)fd, address);
            PUSH(ret);
        }
        break;
    case LIB_SMITE_INIT:
        {
            smite_UWORD stack_size;
            POP((smite_WORD *)&stack_size);
            smite_UWORD memory_size;
            POP((smite_WORD *)&memory_size);
            smite_state *new_smite_state = smite_init((size_t)memory_size, (size_t)stack_size);
            PUSH_NATIVE_TYPE(smite_state *, new_smite_state);
        }
        break;
    case LIB_SMITE_DESTROY:
        {
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            smite_destroy(inner_smite_state);
        }
        break;
    case LIB_SMITE_REGISTER_ARGS:
        {
            char **argv;
            POP_NATIVE_TYPE(char **, &argv);
            smite_WORD argc;
            POP(&argc);
            smite_state *inner_smite_state;
            POP_NATIVE_TYPE(smite_state *, &inner_smite_state);
            int ret = smite_register_args(inner_smite_state, (int)argc, argv);
            PUSH(ret);
        }
        break;
    default:
        RAISE(-15);
    }

    return 0;
}

static int extra_libc(smite_state *S)
{
    smite_UWORD routine;
    POP((smite_WORD *)&routine);
    switch (routine) {
    case LIB_C_ARGC: // ( -- u )
        PUSH(S->main_argc);
        break;
    case LIB_C_ARG_LEN: // ( u1 -- u2 )
        {
            smite_UWORD narg;
            POP((smite_WORD *)&narg);
            if (narg >= (smite_UWORD)S->main_argc)
                PUSH(0);
            else
                PUSH(S->main_argv_len[narg]);
        }
        break;
    case LIB_C_ARG_COPY: // ( u1 c-addr u2 -- u3 )
        {
            smite_UWORD len;
            POP((smite_WORD *)&len);
            smite_UWORD buf;
            POP((smite_WORD *)&buf);
            smite_UWORD narg;
            POP((smite_WORD *)&narg);

            if (narg < (smite_UWORD)S->main_argc) {
                len = MIN(len, S->main_argv_len[narg]);
                uint8_t *ptr = smite_native_address_of_range(S, buf, len);
                if (ptr) {
                    memcpy(ptr, S->main_argv[narg], len);
                    PUSH(len);
                } else
                    PUSH(0);
            } else
                PUSH(0);
        }
        break;
    case LIB_C_STDIN:
        PUSH((smite_WORD)(STDIN_FILENO));
        break;
    case LIB_C_STDOUT:
        PUSH((smite_WORD)(STDOUT_FILENO));
        break;
    case LIB_C_STDERR:
        PUSH((smite_WORD)(STDERR_FILENO));
        break;
    case LIB_C_OPEN_FILE:
        {
            bool binary = false;
            smite_WORD perm_;
            POP(&perm_);
            int perm = getflags(perm_, &binary);
            smite_UWORD str;
            POP((smite_WORD *)&str);
            char *s = (char *)smite_native_address_of_range(S, str, 0);
            int fd = s ? open(s, perm, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            PUSH((smite_WORD)fd);
            PUSH(fd < 0 || (binary && set_binary_mode(fd, O_BINARY) < 0) ? -1 : 0);
        }
        break;
    case LIB_C_CLOSE_FILE:
        {
            smite_WORD fd;
            POP(&fd);
            PUSH((smite_WORD)close(fd));
        }
        break;
    case LIB_C_READ_FILE:
        {
            smite_WORD fd;
            POP(&fd);
            smite_UWORD nbytes;
            POP((smite_WORD *)&nbytes);
            smite_UWORD buf;
            POP((smite_WORD *)&buf);

            ssize_t nread = 0;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nread = read((int)fd, ptr, nbytes);

            PUSH(nread);
            PUSH(nread >= 0 ? 0 : -1);
        }
        break;
    case LIB_C_WRITE_FILE:
        {
            smite_WORD fd;
            POP(&fd);
            smite_UWORD nbytes;
            POP((smite_WORD *)&nbytes);
            smite_UWORD buf;
            POP((smite_WORD *)&buf);

            ssize_t nwritten = 0;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nwritten = write((int)fd, ptr, nbytes);

            PUSH(nwritten);
            PUSH(nwritten >= 0 ? 0 : -1);
        }
        break;
    case LIB_C_FILE_POSITION:
        {
            smite_WORD fd;
            POP(&fd);
            off_t res = lseek((int)fd, 0, SEEK_CUR);
            PUSH_NATIVE_TYPE(off_t, res);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case LIB_C_REPOSITION_FILE:
        {
            smite_WORD fd;
            POP(&fd);
            off_t off;
            POP_NATIVE_TYPE(off_t, &off);
            off_t res = lseek((int)fd, off, SEEK_SET);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case LIB_C_FLUSH_FILE:
        {
            smite_WORD fd;
            POP(&fd);
            int res = fdatasync((int)fd);
            PUSH(res);
        }
        break;
    case LIB_C_RENAME_FILE:
        {
            smite_UWORD str1;
            POP((smite_WORD *)&str1);
            smite_UWORD str2;
            POP((smite_WORD *)&str2);
            char *s1 = (char *)smite_native_address_of_range(S, str1, 0);
            char *s2 = (char *)smite_native_address_of_range(S, str2, 0);
            if (s1 == NULL || s2 == NULL)
                RAISE(-5);
            PUSH(rename(s2, s1));
        }
        break;
    case LIB_C_DELETE_FILE:
        {
            smite_UWORD str;
            POP((smite_WORD *)&str);
            char *s = (char *)smite_native_address_of_range(S, str, 0);
            if (s == NULL)
                RAISE(-5);
            PUSH(remove(s));
        }
        break;
    case LIB_C_FILE_SIZE:
        {
            struct stat st;
            smite_WORD fd;
            POP(&fd);
            int res = fstat((int)fd, &st);
            PUSH_NATIVE_TYPE(off_t, st.st_size);
            PUSH(res);
        }
        break;
    case LIB_C_RESIZE_FILE:
        {
            smite_WORD fd;
            POP(&fd);
            off_t off;
            POP_NATIVE_TYPE(off_t, &off);
            int res = ftruncate((int)fd, off);
            PUSH(res);
        }
        break;
    case LIB_C_FILE_STATUS:
        {
            struct stat st;
            smite_WORD fd;
            POP(&fd);
            int res = fstat((int)fd, &st);
            PUSH(st.st_mode);
            PUSH(res);
        }
        break;
    default:
        RAISE(-15);
        break;
    }

    return 0;
}

int smite_extra(smite_state *S)
{
    switch (S->I) {
    case LIB_SMITE:
        return extra_smite(S);
    case LIB_C:
        return extra_libc(S);
    default:
        return -1;
    }
}
