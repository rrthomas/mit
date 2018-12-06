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
#include "minmax.h"
#include "verify.h"

#include "public.h"
#include "aux.h"
#include "private.h"
#include "opcodes.h"


// Assumption for file functions
verify(sizeof(int) <= sizeof(WORD));


// Check whether a VM address points to a native word-aligned word
#define WORD_IN_ONE_AREA(a)                             \
    (native_address_range_in_one_area((a), WORD_W, false) != NULL)

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


// Perform one pass of the execution cycle
WORD single_step(void)
{
    int exception = 0;
    WORD temp = 0, temp2 = 0;
    BYTE byte = 0;

    int type = decode_instruction(&PC, &I);
    switch (type) {
    case INSTRUCTION_NUMBER:
        PUSH(I);
        break;
    case INSTRUCTION_ACTION:
        switch (I) {
        case O_NOP:
            break;
        case O_POP:
            {
                WORD depth = POP;
                SP -= depth * WORD_W * STACK_DIRECTION;
            }
            break;
        case O_SWAP:
            {
                WORD depth = POP;
                WORD swapee = LOAD_WORD(SP - depth * WORD_W * STACK_DIRECTION);
                WORD top = POP;
                PUSH(swapee);
                STORE_WORD(SP - depth * WORD_W * STACK_DIRECTION, top);
            }
            break;
        case O_PUSH:
            {
                WORD depth = POP;
                WORD pickee = LOAD_WORD(SP - depth * WORD_W * STACK_DIRECTION);
                PUSH(pickee);
            }
            break;
        case O_RPUSH:
            {
                WORD depth = POP;
                WORD pickee = LOAD_WORD(RP - depth * WORD_W * STACK_DIRECTION);
                PUSH(pickee);
            }
            break;
        case O_POP2R:
            {
                WORD value = POP;
                PUSH_RETURN(value);
            }
            break;
        case O_RPOP:
            {
                WORD value = POP_RETURN;
                PUSH(value);
            }
            break;
        case O_LT:
            {
                WORD a = POP;
                WORD b = POP;
                PUSH(b < a ? PACKAGE_UPPER_TRUE : PACKAGE_UPPER_FALSE);
            }
            break;
        case O_EQ:
            {
                WORD a = POP;
                WORD b = POP;
                PUSH(a == b ? PACKAGE_UPPER_TRUE : PACKAGE_UPPER_FALSE);
            }
            break;
        case O_ULT:
            {
                UWORD a = POP;
                UWORD b = POP;
                PUSH(b < a ? PACKAGE_UPPER_TRUE : PACKAGE_UPPER_FALSE);
            }
            break;
        case O_ADD:
            {
                WORD a = POP;
                WORD b = POP;
                PUSH(b + a);
            }
            break;
        case O_MUL:
            {
                WORD multiplier = POP;
                WORD multiplicand = POP;
                PUSH(multiplier * multiplicand);
            }
            break;
        case O_UDIVMOD:
            {
                UWORD divisor = POP;
                UWORD dividend = POP;
                DIVZERO(divisor);
                PUSH(dividend / divisor);
                PUSH(dividend % divisor);
            }
            break;
        case O_DIVMOD:
            {
                WORD divisor = POP;
                WORD dividend = POP;
                DIVZERO(divisor);
                PUSH(dividend / divisor);
                PUSH(dividend % divisor);
            }
            break;
        case O_NEGATE:
            {
                WORD a = POP;
                PUSH(-a);
            }
            break;
        case O_INVERT:
            {
                WORD a = POP;
                PUSH(~a);
            }
            break;
        case O_AND:
            {
                WORD a = POP;
                WORD b = POP;
                PUSH(a & b);
            }
            break;
        case O_OR:
            {
                WORD a = POP;
                WORD b = POP;
                PUSH(a | b);
            }
            break;
        case O_XOR:
            {
                WORD a = POP;
                WORD b = POP;
                PUSH(a ^ b);
            }
            break;
        case O_LSHIFT:
            {
                WORD shift = POP;
                WORD value = POP;
                PUSH(shift < (WORD)WORD_BIT ? value << shift : 0);
            }
            break;
        case O_RSHIFT:
            {
                WORD shift = POP;
                WORD value = POP;
                PUSH(shift < (WORD)WORD_BIT ? (WORD)((UWORD)value >> shift) : 0);
            }
            break;
        case O_LOAD:
            {
                WORD addr = POP;
                WORD value = LOAD_WORD(addr);
                PUSH(value);
            }
            break;
        case O_STORE:
            {
                WORD addr = POP;
                WORD value = POP;
                STORE_WORD(addr, value);
            }
            break;
        case O_LOADB:
            {
                WORD addr = POP;
                BYTE value = LOAD_BYTE(addr);
                PUSH((WORD)value);
            }
            break;
        case O_STOREB:
            {
                WORD addr = POP;
                BYTE value = (BYTE)POP;
                STORE_BYTE(addr, value);
            }
            break;
        case O_PUSH_SP:
            {
                WORD value = SP;
                PUSH(value);
            }
            break;
        case O_STORE_SP:
            {
                WORD value = POP;
                CHECK_ALIGNED(value);
                if (exception == 0)
                    SP = value;
            }
            break;
        case O_PUSH_RP:
            PUSH(RP);
            break;
        case O_STORE_RP:
            {
                WORD value = POP;
                CHECK_ALIGNED(value);
                if (exception == 0)
                    RP = value;
            }
            break;
        case O_BRANCH:
            PC = POP;
            break;
        case O_BRANCHZ:
            {
                WORD addr = POP;
                if (POP == PACKAGE_UPPER_FALSE)
                    PC = addr;
                break;
            }
        case O_CALL:
            PUSH_RETURN(PC);
            PC = POP;
            break;
        case O_RET:
            PC = POP_RETURN;
            break;
        case O_PUSH_PSIZE:
            PUSH(POINTER_W);
            break;
        case O_THROW:
            exception = POP;
            break;
        case O_HALT:
            return POP;
        case O_PUSH_PC:
            PUSH(PC);
            break;
        case O_PUSH_S0:
            PUSH(S0);
            break;
        case O_PUSH_SSIZE:
            PUSH(HASHS);
            break;
        case O_PUSH_R0:
            PUSH(R0);
            break;
        case O_PUSH_RSIZE:
            PUSH(HASHR);
            break;
        case O_PUSH_HANDLER:
            PUSH(HANDLER);
            break;
        case O_STORE_HANDLER:
            HANDLER = POP;
            break;
        case O_PUSH_MEMORY:
            PUSH(MEMORY);
            break;
        case O_PUSH_BADPC:
            PUSH(BADPC);
            break;
        case O_PUSH_INVALID:
            PUSH(INVALID);
            break;
        case O_CALL_NATIVE:
            {
                WORD_pointer address;
                for (int i = POINTER_W - 1; i >= 0; i--)
                    address.words[i] = POP;
                address.pointer();
            }
            break;
        case O_EXTRA:
            {
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
                        PUSH_DOUBLE((DUWORD)res);
                        PUSH(res >= 0 ? 0 : -1);
                    }
                    break;
                case OX_REPOSITION_FILE:
                    {
                        int fd = POP;
                        DUWORD ud = POP_DOUBLE;
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
                        PUSH_DOUBLE(st.st_size);
                        PUSH(res);
                    }
                    break;
                case OX_RESIZE_FILE:
                    {
                        int fd = POP;
                        DUWORD ud = POP_DOUBLE;
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
            break;

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
        SP += WORD_W * STACK_DIRECTION;
        if (!WORD_IN_ONE_AREA(SP) || !IS_ALIGNED(SP))
            return -257;
        int store_exception = store_word(SP, exception);
        assert(store_exception == 0);
        BADPC = PC - 1;
        PC = HANDLER;
    }
    return -259; // terminated OK
}
