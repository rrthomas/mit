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
verify(sizeof(int) <= sizeof(CELL));


// Check whether a VM address points to a native cell-aligned cell
#define CELL_IN_ONE_AREA(a)                             \
    (native_address_range_in_one_area((a), CELL_W, false) != NULL)

#define CHECK_ALIGNED_WHOLE_CELL(a)                     \
    CHECK_ADDRESS(a, IS_ALIGNED(a), -23, badadr)        \
    CHECK_ADDRESS(a, CELL_IN_ONE_AREA(a), -9, badadr)


#define DIVZERO(x)                              \
    if (x == 0) {                               \
        PUSH(-10);                              \
        goto throw;                             \
    }


// I/O support

// Copy a string from VM to native memory
static int getstr(UCELL adr, UCELL len, char **res)
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
static int getflags(UCELL perm, bool *binary)
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
static UCELL *main_argv;
static UCELL *main_argv_len;
int register_args(int argc, char *argv[])
{
    main_argc = argc;
    if ((main_argv = calloc(argc, sizeof(UCELL))) == NULL ||
        (main_argv_len = calloc(argc, sizeof(UCELL))) == NULL)
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
CELL single_step(void)
{
    int exception = 0;
    CELL temp = 0, temp2 = 0;
    BYTE byte = 0;

    I = (BYTE)A;
    ARSHIFT(A, 8);
    switch (I) {
    case O_NEXT00:
    case O_NEXTFF:
 next:
        EP += CELL_W;
        exception = load_cell(EP - CELL_W, &A);
        break;
    case O_DROP:
        {
            CELL depth = POP;
            SP -= depth * CELL_W * STACK_DIRECTION;
        }
        break;
    case O_SWAP:
        {
            CELL depth = POP;
            CELL swapee = LOAD_CELL(SP - depth * CELL_W * STACK_DIRECTION);
            CELL top = POP;
            PUSH(swapee);
            STORE_CELL(SP - depth * CELL_W * STACK_DIRECTION, top);
        }
        break;
    case O_DUP:
        {
            CELL depth = POP;
            CELL pickee = LOAD_CELL(SP - depth * CELL_W * STACK_DIRECTION);
            PUSH(pickee);
        }
        break;
    case O_RDUP:
        {
            CELL depth = POP;
            CELL pickee = LOAD_CELL(RP - depth * CELL_W * STACK_DIRECTION);
            PUSH(pickee);
        }
        break;
    case O_TOR:
        {
            CELL value = POP;
            PUSH_RETURN(value);
        }
        break;
    case O_RFROM:
        {
            CELL value = POP_RETURN;
            PUSH(value);
        }
        break;
    case O_LESS:
        {
            CELL a = POP;
            CELL b = POP;
            PUSH(b < a ? PACKAGE_UPPER_TRUE : PACKAGE_UPPER_FALSE);
        }
        break;
    case O_EQUAL:
        {
            CELL a = POP;
            CELL b = POP;
            PUSH(a == b ? PACKAGE_UPPER_TRUE : PACKAGE_UPPER_FALSE);
        }
        break;
    case O_ULESS:
        {
            UCELL a = POP;
            UCELL b = POP;
            PUSH(b < a ? PACKAGE_UPPER_TRUE : PACKAGE_UPPER_FALSE);
        }
        break;
    case O_PLUS:
        {
            CELL a = POP;
            CELL b = POP;
            PUSH(b + a);
        }
        break;
    case O_STAR:
        {
            CELL multiplier = POP;
            CELL multiplicand = POP;
            PUSH(multiplier * multiplicand);
        }
        break;
    case O_UMODSLASH:
        {
            UCELL divisor = POP;
            UCELL dividend = POP;
            DIVZERO(divisor);
            PUSH(dividend / divisor);
            PUSH(dividend % divisor);
        }
        break;
    case O_SREMSLASH:
        {
            CELL divisor = POP;
            CELL dividend = POP;
            DIVZERO(divisor);
            PUSH(dividend / divisor);
            PUSH(dividend % divisor);
        }
        break;
    case O_NEGATE:
        {
            CELL a = POP;
            PUSH(-a);
        }
        break;
    case O_INVERT:
        {
            CELL a = POP;
            PUSH(~a);
        }
        break;
    case O_AND:
        {
            CELL a = POP;
            CELL b = POP;
            PUSH(a & b);
        }
        break;
    case O_OR:
        {
            CELL a = POP;
            CELL b = POP;
            PUSH(a | b);
        }
        break;
    case O_XOR:
        {
            CELL a = POP;
            CELL b = POP;
            PUSH(a ^ b);
        }
        break;
    case O_LSHIFT:
        {
            CELL shift = POP;
            CELL value = POP;
            PUSH(shift < (CELL)CELL_BIT ? value << shift : 0);
        }
        break;
    case O_RSHIFT:
        {
            CELL shift = POP;
            CELL value = POP;
            PUSH(shift < (CELL)CELL_BIT ? (CELL)((UCELL)value >> shift) : 0);
        }
        break;
    case O_FETCH:
        {
            CELL addr = POP;
            CELL value = LOAD_CELL(addr);
            PUSH(value);
        }
        break;
    case O_STORE:
        {
            CELL addr = POP;
            CELL value = POP;
            STORE_CELL(addr, value);
        }
        break;
    case O_CFETCH:
        {
            CELL addr = POP;
            BYTE value = LOAD_BYTE(addr);
            PUSH((CELL)value);
        }
        break;
    case O_CSTORE:
        {
            CELL addr = POP;
            BYTE value = (BYTE)POP;
            STORE_BYTE(addr, value);
        }
        break;
    case O_SPFETCH:
        {
            CELL value = SP;
            PUSH(value);
        }
        break;
    case O_SPSTORE:
        {
            CELL value = POP;
            CHECK_ALIGNED(value);
            SP = value;
        }
        break;
    case O_RPFETCH:
        PUSH(RP);
        break;
    case O_RPSTORE:
        {
            CELL value = POP;
            CHECK_ALIGNED(value);
            RP = value;
        }
        break;
    case O_EPSTORE:
        {
            CELL addr = POP;
            CHECK_ALIGNED_WHOLE_CELL(addr);
            EP = addr;
            goto next;
        }
        break;
    case O_QEPSTORE:
        {
            CELL addr = POP;
            if (POP == PACKAGE_UPPER_FALSE) {
                CHECK_ALIGNED_WHOLE_CELL(addr);
                EP = addr;
                goto next;
            }
            break;
        }
    case O_EXECUTE:
        {
            CELL addr = POP;
            CHECK_ALIGNED_WHOLE_CELL(addr);
            PUSH_RETURN(EP);
            EP = addr;
            goto next;
        }
        break;
    case O_EXIT:
        {
            CELL addr = POP_RETURN;
            CHECK_ALIGNED_WHOLE_CELL(addr);
            EP = addr;
            goto next;
        }
        break;
    case O_LITERAL:
        PUSH(LOAD_CELL(EP));
        EP += CELL_W;
        break;
 throw:
    case O_THROW:
        // exception may already be set, so CELL_STORE may have no effect here.
        BAD = EP;
        if (!CELL_IN_ONE_AREA(THROW) || !IS_ALIGNED(THROW))
            return -258;
        EP = THROW;
        exception = 0; // Any exception has now been dealt with
        goto next;
        break;
    case O_HALT:
        return POP;
    case O_EPFETCH:
        PUSH(EP);
        break;
    case O_S0FETCH:
        PUSH(S0);
        break;
    case O_HASHS:
        PUSH(HASHS);
        break;
    case O_R0FETCH:
        PUSH(R0);
        break;
    case O_HASHR:
        PUSH(HASHR);
        break;
    case O_THROWFETCH:
        PUSH(THROW);
        break;
    case O_THROWSTORE:
        {
            CELL value = POP;
            CHECK_ALIGNED(value);
            THROW = value;
        }
        break;
    case O_MEMORYFETCH:
        PUSH(MEMORY);
        break;
    case O_BADFETCH:
        PUSH(BAD);
        break;
    case O_NOT_ADDRESSFETCH:
        PUSH(NOT_ADDRESS);
        break;
    case O_LINK:
        {
            CELL_pointer address;
            for (int i = POINTER_W - 1; i >= 0; i--)
                address.cells[i] = POP;
            address.pointer();
        }
        break;

    case OX_ARGC: // ( -- u )
        PUSH(main_argc);
        break;
    case OX_ARG: // ( u1 -- c-addr u2 )
        {
            UCELL narg = POP;
            if (narg >= (UCELL)main_argc) {
                PUSH(0);
                PUSH(0);
            } else {
                PUSH(main_argv[narg]);
                PUSH(main_argv_len[narg]);
            }
        }
        break;
    case OX_STDIN:
        PUSH((CELL)(STDIN_FILENO));
        break;
    case OX_STDOUT:
        PUSH((CELL)(STDOUT_FILENO));
        break;
    case OX_STDERR:
        PUSH((CELL)(STDERR_FILENO));
        break;
    case OX_OPEN_FILE:
        {
            bool binary = false;
            int perm = getflags(POP, &binary);
            UCELL len = POP;
            UCELL str = POP;
            char *file;
            exception = getstr(str, len, &file);
            int fd = exception == 0 ? open(file, perm, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            free(file);
            PUSH((CELL)fd);
            PUSH(fd < 0 || (binary && set_binary_mode(fd, O_BINARY) < 0) ? -1 : 0);
        }
        break;
    case OX_CLOSE_FILE:
        {
            int fd = POP;
            PUSH((CELL)close(fd));
        }
        break;
    case OX_READ_FILE:
        {
            int fd = POP;
            UCELL nbytes = POP;
            UCELL buf = POP;

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
            UCELL nbytes = POP;
            UCELL buf = POP;

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
            PUSH_DOUBLE((DUCELL)res);
            PUSH(res >= 0 ? 0 : -1);
        }
        break;
    case OX_REPOSITION_FILE:
        {
            int fd = POP;
            DUCELL ud = POP_DOUBLE;
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
            UCELL len1 = POP;
            UCELL str1 = POP;
            UCELL len2 = POP;
            UCELL str2 = POP;
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
            UCELL len = POP;
            UCELL str = POP;
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
            DUCELL ud = POP_DOUBLE;
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
        PUSH(-256);
        goto throw;
    }
    if (exception == 0)
        return -259; // terminated OK

    // Deal with address exceptions during execution cycle.
    // Since we have already had an exception, and must return a different
    // code from usual if SP is now invalid, push the exception code
    // "manually".
 badadr:
    SP += CELL_W * STACK_DIRECTION;
    if (!CELL_IN_ONE_AREA(SP) || !IS_ALIGNED(SP))
      return -257;
    store_cell(SP, exception);
    goto throw;
}
