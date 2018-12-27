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
#include "opcodes.h"


// Assumption for file functions
verify(sizeof(int) <= sizeof(WORD));


// Check whether a VM address points to a native word-aligned word
#define WORD_IN_ONE_AREA(a)                             \
    (native_address_range_in_one_area(S, (a), WORD_SIZE, false) != NULL)

#define DIVZERO(x)                              \
    if (x == 0)                                 \
        exception = -10;


// I/O support

// Copy a string from VM to native memory
static int getstr(state *S, UWORD adr, UWORD len, char **res)
{
    int exception = 0;

    *res = calloc(1, len + 1);
    if (*res == NULL)
        exception = -511;
    else
        for (size_t i = 0; exception == 0 && i < len; i++, adr++) {
            exception = load_byte(S, adr, (BYTE *)((*res) + i));
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
int register_args(state *S, int argc, char *argv[])
{
    S->main_argc = argc;
    if ((S->main_argv = calloc(argc, sizeof(UWORD))) == NULL ||
        (S->main_argv_len = calloc(argc, sizeof(UWORD))) == NULL)
        return -1;

    for (int i = 0; i < argc; i++) {
        size_t len = strlen(argv[i]);
        S->main_argv[i] = mem_allot(S, argv[i], len, true);
        if (S->main_argv[i] == 0)
            return -2;
        S->main_argv_len[i] = len;
    }
    return 0;
}

static int extra_smite(state *S)
{
    int exception = 0;

    WORD temp = 0;
    switch (POP) {
    case OX_SMITE_CURRENT_STATE:
        PUSH_NATIVE_POINTER(S);
        break;
    case OX_SMITE_LOAD_WORD:
        {
            UWORD addr = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            WORD value;
            int ret = load_word(inner_state, addr, &value);
            PUSH(value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_STORE_WORD:
        {
            WORD value = POP;
            UWORD addr = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = store_word(inner_state, addr, value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_LOAD_BYTE:
        {
            UWORD addr = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            BYTE value;
            int ret = load_byte(inner_state, addr, &value);
            PUSH(value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_STORE_BYTE:
        {
            BYTE value = POP;
            UWORD addr = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = store_byte(inner_state, addr, value);
            PUSH(ret);
        }
        break;
    case OX_SMITE_PRE_DMA:
        {
            bool write = POP;
            UWORD to = POP;
            UWORD from = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = pre_dma(inner_state, from, to, write);
            PUSH(ret);
        }
        break;
    case OX_SMITE_POST_DMA:
        {
            UWORD to = POP;
            UWORD from = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = post_dma(inner_state, from, to);
            PUSH(ret);
        }
        break;
    case OX_SMITE_MEM_HERE:
        {
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            UWORD addr = mem_here(inner_state);
            PUSH(addr);
        }
        break;
    case OX_SMITE_MEM_ALLOT:
        {
            bool writable = POP;
            size_t n = POP;
            void *p;
            POP_NATIVE_POINTER(p);
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            UWORD addr = mem_allot(inner_state, p, n, writable);
            PUSH(addr);
        }
        break;
    case OX_SMITE_MEM_ALIGN:
        {
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            UWORD addr = mem_align(inner_state);
            PUSH(addr);
        }
        break;
    case OX_SMITE_NATIVE_ADDRESS:
        {
            bool writable = POP;
            UWORD addr = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            uint8_t *ptr = native_address(inner_state, addr, writable);
            PUSH_NATIVE_POINTER(ptr);
        }
        break;
    case OX_SMITE_RUN:
        {
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = run(inner_state);
            PUSH(ret);
        }
        break;
    case OX_SMITE_SINGLE_STEP:
        {
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = single_step(inner_state);
            PUSH(ret);
        }
        break;
    case OX_SMITE_LOAD_OBJECT:
        {
            UWORD address = POP;
            int fd = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = load_object(inner_state, fd, address);
            PUSH(ret);
        }
        break;
    case OX_SMITE_INIT:
        {
            size_t return_stack_size = POP;
            size_t stack_size = POP;
            size_t memory_size = POP;
            state *new_state = init(memory_size, stack_size, return_stack_size);
            PUSH_NATIVE_POINTER(new_state);
        }
        break;
    case OX_SMITE_DESTROY:
        {
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            destroy(inner_state);
        }
        break;
    case OX_SMITE_REGISTER_ARGS:
        {
            char **argv;
            POP_NATIVE_POINTER(argv);
            int argc = POP;
            state *inner_state;
            POP_NATIVE_POINTER(inner_state);
            int ret = register_args(inner_state, argc, argv);
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
    WORD temp = 0;
#if WORD_SIZE == 4
    WORD temp2 = 0;
#endif

    switch (POP) {
    case OX_ARGC: // ( -- u )
        PUSH(S->main_argc);
        break;
    case OX_ARG: // ( u1 -- c-addr u2 )
        {
            UWORD narg = POP;
            if (narg >= (UWORD)S->main_argc) {
                PUSH(0);
                PUSH(0);
            } else {
                PUSH(S->main_argv[narg]);
                PUSH(S->main_argv_len[narg]);
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
            exception = getstr(S, str, len, &file);
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
                exception = pre_dma(S, buf, buf + nbytes, true);
                if (exception == 0) {
                    res = read(fd, native_address(S, buf, true), nbytes);
                    exception = post_dma(S, buf, buf + nbytes);
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
                exception = pre_dma(S, buf, buf + nbytes, false);
                if (exception == 0) {
                    res = write(fd, native_address(S, buf, false), nbytes);
                    exception = post_dma(S, buf, buf + nbytes);
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
            exception = getstr(S, str2, len2, &from) ||
                getstr(S, str1, len1, &to) ||
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
            exception = getstr(S, str, len, &file) ||
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
    default:
        exception = -260;
        break;
    }

    return exception;
}

static int extra(state *S)
{
    int exception = 0;
    WORD temp = 0;

    switch (POP) {
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
    WORD temp = 0;
    BYTE byte = 0;

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
        // Since we have already had an exception, and must return a different
        // code from usual if SP is now invalid, push the exception code
        // "manually".
        S->SP += WORD_SIZE * STACK_DIRECTION;
        S->BADPC = S->PC - 1;
        if (!WORD_IN_ONE_AREA(S->SP) || !IS_ALIGNED(S->SP))
            return -257;
        int store_exception = store_word(S, S->SP, exception);
        assert(store_exception == 0);
        S->PC = S->HANDLER;
    }
    return -258; // terminated OK
}
