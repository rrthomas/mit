// Front-end and shell.
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "external_syms.h"

#include <stdlib.h>
#include <stdarg.h>
#include <inttypes.h>
#include <errno.h>
#include <ctype.h>
#include <string.h>
#include <setjmp.h>
#include <unistd.h>
#include <getopt.h>
#include <sys/wait.h>
#include <libgen.h>
#include <glob.h>

#include "progname.h"
#include "xalloc.h"
#include "xvasprintf.h"

#include "public.h"
#include "aux.h"
#include "debug.h"
#include "opcodes.h"


#define DEFAULT_MEMORY 1048576 // Default size of VM memory in cells (4Mb)
#define MAX_MEMORY 536870912 // Maximum size of memory in cells (2Gb)
static UCELL memory_size = DEFAULT_MEMORY; // Size of VM memory in cells
CELL *memory;

#define MAXLEN 80   // Maximum input line length

static bool interactive;
static unsigned long lineno;
static jmp_buf env;

static bool debug_on_error = false;

static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 0) void verror(const char *format, va_list args)
{
    if (!interactive)
        fprintf(stderr, PACKAGE ":%lu: ", lineno);
    vfprintf(stderr, format, args);
    fprintf(stderr, "\n");
}

static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void warn(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
}

static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void fatal(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
    longjmp(env, 1);
}

static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void die(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
    exit(1);
}

static const char *command[] = {
#define C(cmd) #cmd,
#include "tbl_commands.h"
#undef C
};
enum commands {
#define C(cmd) c_##cmd,
#include "tbl_commands.h"
#undef C
};
static int commands = sizeof(command) / sizeof(*command);

static const char *regist[] = {
#define R(reg) #reg,
#include "tbl_registers.h"
#undef R
};
enum registers {
#define R(reg) r_##reg,
#include "tbl_registers.h"
#undef R
};
static int registers = sizeof(regist) / sizeof(*regist);

static long count[256];


static const char *globfile(const char *file)
{
    static glob_t globbuf;
    static bool first_time = true;
    if (!first_time)
        globfree(&globbuf);
    first_time = false;

    if (glob(file, GLOB_TILDE_CHECK, NULL, &globbuf) != 0)
        fatal("cannot find file '%s'", file);
    else if (globbuf.gl_pathc != 1)
        fatal("'%s' matches more than one file", file);
    return globbuf.gl_pathv[0];
}

static const char *globdirname(const char *file)
{
    static char *globbed_file = NULL;
    free(globbed_file);

    if (strchr(file, '/') == NULL)
        return file;

    char *filecopy = xstrdup(file);
    const char *dir = globfile(dirname(filecopy));
    free(filecopy);
    filecopy = xstrdup(file);
    char *base = basename(filecopy);
    globbed_file = xasprintf("%s/%s", dir, base);
    free(filecopy);

    return globbed_file;
}

static void check_valid(UCELL adr, const char *quantity)
{
    if (native_address(adr, false) == NULL)
        fatal("%s is invalid", quantity);
}

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wsuggest-attribute=pure"
static void check_aligned(UCELL adr, const char *quantity)
{
    if (!IS_ALIGNED(adr))
        fatal("%s must be cell-aligned", quantity);
}
#pragma GCC diagnostic pop

static void check_range(UCELL start, UCELL end, const char *quantity)
{
    check_valid(start, quantity);
    check_valid(end, quantity);
    if (start >= end)
        fatal("start address must be less than end address");
}

static void upper(char *s)
{
    size_t len = strlen(s);

    for (size_t i = 0; i < len; i++, s++)
        *s = toupper(*s);
}

static size_t search(const char *token, const char *list[], size_t entries)
{
    size_t len = strlen(token);

    for (size_t i = 0; i < entries; i++) {
        size_t entry_len = strlen(list[i]);
        if (entry_len > 1 && len == 1)
            continue;
        if (strncmp(token, list[i], len) == 0)
            return i;
    }

    return SIZE_MAX;
}

static BYTE parse_instruction(const char *token)
{
    BYTE opcode = O_UNDEFINED;
    if (token[0] == 'O') {
        opcode = toass(token + 1);
        if (opcode == O_UNDEFINED)
            fatal("invalid opcode");
    }
    return opcode;
}

static long parse_number(const char *s, char **endp)
{
    return s[0] == '$' ? strtol(s + 1, endp, 16) :
        strtol(s, endp, 10);
}

static long single_arg(const char *s, int *bytes)
{
    if (s == NULL)
        fatal("too few arguments");

    char *endp;
    long n = parse_number(s, &endp);

    if (endp != &s[strlen(s)])
        fatal("invalid number");

    if (bytes != NULL)
        *bytes = byte_size(n);

    return n;
}

static void double_arg(char *s, long *start, long *end, bool default_args)
{
    bool plus = default_args;

    char *token, copy[MAXLEN];
    if (s == NULL || (token = strtok(strcpy(copy, s), " +")) == NULL) {
        if (!default_args)
            fatal("too few arguments");
    } else {
        size_t i;
        for (i = strlen(token); s[i] == ' ' && i < strlen(s); i++)
            ;

        plus = plus || (i < strlen(s) && s[i] == '+');

        *start = single_arg(token, NULL);

        if ((token = strtok(NULL, " +")) == NULL) {
            if (!default_args)
                fatal("too few arguments");
        } else
            *end = single_arg(token, NULL);
    }

    if (plus)
        *end += *start;
}


static int load_op(BYTE o)
{
    return o == O_BRANCH || o == O_QBRANCH || o == O_CALL || o == O_LOOP ||
        o == O_PLOOP || o == O_LITERAL;
}

static int imm_op(BYTE o)
{
    return load_op(o & 0xfe);
}

static void disassemble(UCELL start, UCELL end)
{
    for (UCELL p = start; p < end; ) {
        printf("$%08"PRIX32": ", p);
        CELL a;
        load_cell(p, &a);
        p += CELL_W;

        do {
            BYTE i = (BYTE)a;
            ARSHIFT(a, 8);
            const char *token = disass(i);
            if (strcmp(token, ""))
                printf("%s", token);
            else
                printf("Undefined instruction");

            if (load_op(i)) {
                CELL lit;
                load_cell(p, &lit);
                if (i != O_LITERAL)
                    printf(" $%"PRIX32, (UCELL)lit);
                else
                    printf(" %"PRId32" ($%"PRIX32")", lit, (UCELL)lit);
                p += CELL_W;
            } else {
                if (imm_op(i)) {
                    if (i != O_LITERALI)
                        printf(" $%"PRIX32, p + a * CELL_W);
                    else
                        printf(" %"PRId32" ($%"PRIX32")", a, (UCELL)a);
                    a = 0;
                }
            }

            printf("\n");
            if (a == 0 || a == -1)
                break;
            printf("           ");
        } while (1);
    }
}


static void reinit(void)
{
    memset(count, 0, 256 * sizeof(long));
    init(memory, memory_size);
    start_ass(EP);
}


static int save_object(FILE *file, UCELL address, UCELL length)
{
    uint8_t *ptr = native_address_range_in_one_area(address, length, false);
    if (!IS_ALIGNED(address) || ptr == NULL)
        return -1;

    if (fputs(PACKAGE_UPPER, file) == EOF ||
        putc('\0', file) == EOF ||
        putc((char)ENDISM, file) == EOF ||
        fwrite(&length, CELL_W, 1, file) != 1 ||
        fwrite(ptr, CELL_W, length, file) != length)
        return -3;

    return 0;
}


static void do_assign(char *token)
{
    char *number = strtok(NULL, " ");
    long value;
    int bytes = 4;

    upper(number);
    value = parse_instruction(number);
    if (value != O_UNDEFINED)
        bytes = 1;
    else
        value = single_arg(number, &bytes);

    int no = search(token, regist, registers);
    switch (no) {
        case r_A:
            A = value;
            break;
        case r_NOT_ADDRESS:
            NOT_ADDRESS = value;
            break;
        case r_BAD:
            BAD = value;
            break;
        case r_CHECKED:
        case r_ENDISM:
        case r_MEMORY:
            fatal("cannot assign to %s", regist[no]);
            break;
        case r_EP:
            EP = value;
            start_ass(EP);
            break;
        case r_I:
            if (bytes > 1)
                fatal("only one byte can be assigned to I");
            I = value;
            break;
        case r_RP:
            RP = value;
            break;
        case r_R0:
            R0 = value;
            break;
        case r_SP:
            SP = value;
            break;
        case r_S0:
            S0 = value;
            break;
        case r_THROW:
            THROW = value;
        default:
            {
                CELL adr = (CELL)single_arg(token, NULL);

                check_valid(adr, "Address");
                if (!IS_ALIGNED(adr) && bytes > 1)
                    fatal("only a byte can be assigned to an unaligned address");
                if (bytes == 1)
                    store_byte(adr, value);
                else
                    store_cell(adr, value);
            }
    }
}

static void do_display(size_t no, const char *format)
{
    char *display;

    switch (no) {
        case r_A:
            display = xasprintf("A = $%"PRIX32, (UCELL)A);
            break;
        case r_NOT_ADDRESS:
            display = xasprintf("-ADDRESS = $%"PRIX32" (%"PRIu32")", NOT_ADDRESS, NOT_ADDRESS);
            break;
        case r_BAD:
            display = xasprintf("'BAD = $%"PRIX32" (%"PRIu32")", BAD, BAD);
            break;
        case r_CHECKED:
            display = xasprintf("CHECKED = %d", CHECKED);
            break;
        case r_ENDISM:
            display = xasprintf("ENDISM = %d", ENDISM);
            break;
        case r_EP:
            display = xasprintf("EP = $%"PRIX32" (%"PRIu32")", EP, EP);
            break;
        case r_I:
            display = xasprintf("I = %-10s ($%02X)", disass(I), I);
            break;
        case r_MEMORY:
            display = xasprintf("MEMORY = $%"PRIX32" (%"PRIu32")", MEMORY, MEMORY);
            break;
        case r_RP:
            display = xasprintf("RP = $%"PRIX32" (%"PRIu32")", RP, RP);
            break;
        case r_R0:
            display = xasprintf("R0 = $%"PRIX32" (%"PRIu32")", R0, R0);
            break;
        case r_SP:
            display = xasprintf("SP = $%"PRIX32" (%"PRIu32")", SP, SP);
            break;
        case r_S0:
            display = xasprintf("S0 = $%"PRIX32" (%"PRIu32")", S0, S0);
            break;
        case r_THROW:
            display = xasprintf("'THROW = $%"PRIX32" (%"PRIu32")", THROW, THROW);
            break;
        default:
            display = xasprintf("unknown register");
            break;
    }
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wformat-nonliteral"
    printf(format, display);
#pragma GCC diagnostic pop
    free(display);
}

static void do_registers(void)
{
    do_display(r_EP, "%-25s");
    do_display(r_I, "%-22s");
    do_display(r_A, "%-16s\n");
}

static void do_command(int no)
{
    int exception = 0;
    CELL temp = 0;

    switch (no) {
    case c_TOD:
        {
            long value = single_arg(strtok(NULL, " "), NULL);
            PUSH(value);
        }
        break;
    case c_TOR:
        {
            long value = single_arg(strtok(NULL, " "), NULL);
            PUSH_RETURN(value);
        }
        break;
    case c_COUNTS:
        {
            for (int i = 0; i < 92; i++) {
                printf("%10s: %7ld", disass(i), count[i]);
                if ((i + 1) % 4)
                    putchar(' ');
                else
                    putchar('\n');
            }
            printf("%10s: %7ld\n", disass(255), count[255]);
        }
        break;
    case c_DISASSEMBLE:
        {
            long start = EP - 16, end = 64;

            double_arg(strtok(NULL, ""), &start, &end, true);
            check_aligned(start, "Address");
            check_aligned(end, "Address");
            check_range(start, end, "Address");
            disassemble((UCELL)start, (UCELL)end);
        }
        break;
    case c_DFROM:
        {
            CELL value = POP;
            printf("%"PRId32" ($%"PRIX32")\n", value, (UCELL)value);
        }
        break;
    case c_DATA:
    case c_STACKS:
        show_data_stack();
        if (no == c_STACKS)
            goto c_ret;
        break;
    case c_DUMP:
        {
            long start = EP - 64, end = 256;
            double_arg(strtok(NULL, ""), &start, &end, true);
            check_range(start, end, "Address");
            while (start < end) {
                printf("$%08lX ", (unsigned long)start);
                const int chunk = 16;
                char ascii[chunk];
                for (int i = 0; i < chunk && start < end; i++) {
                    BYTE byte;
                    load_byte(start + i, &byte);
                    if (i % 8 == 0)
                        putchar(' ');
                    printf("%02X ", byte);
                    ascii[i] = isprint(byte) ? byte : '.';
                }
                start += chunk;
                printf(" |%.*s|\n", chunk, ascii);
            }
        }
        break;
    case c_FROM:
        {
            char *arg = strtok(NULL, " ");
            if (arg != NULL) {
                long adr = single_arg(arg, NULL);
                EP = adr;
            }
            NEXT;
        }
        break;
    case c_INITIALISE:
        reinit();
        break;
    case c_LOAD:
        {
            reinit();

            const char *file = strtok(NULL, " ");
            long adr = 0;
            char *arg = strtok(NULL, " ");
            if (arg != NULL)
                adr = single_arg(arg, NULL);

            FILE *handle = fopen(globfile(file), "rb");
            if (handle == NULL)
                fatal("cannot open file '%s'", file);
            int ret = load_object(handle, adr);
            fclose(handle);

            switch (ret) {
            case -1:
                fatal("address out of range or unaligned, or module too large");
                break;
            case -2:
                fatal("module header invalid");
                break;
            case -3:
                fatal("error while loading module");
                break;
            default:
                break;
            }
        }
        break;
    case c_QUIT:
        exit(0);
    case c_REGISTERS:
        do_registers();
        break;
    case c_RFROM:
        {
            CELL value = POP_RETURN;
            printf("$%"PRIX32" (%"PRId32")\n", (UCELL)value, value);
        }
        break;
    c_ret:
    case c_RETURN:
        show_return_stack();
        break;
    case c_RUN:
        printf("HALT code %"PRId32" was returned\n", run());
        break;
    case c_STEP:
    case c_TRACE:
        {
            char *arg = strtok(NULL, " ");
            CELL ret = -259;

            if (arg == NULL) {
                if ((ret = single_step()))
                    printf("HALT code %"PRId32" was returned\n", ret);
                if (no == c_TRACE) do_registers();
                count[I]++;
            } else {
                upper(arg);
                if (strcmp(arg, "TO") == 0) {
                    unsigned long limit = single_arg(strtok(NULL, ""), NULL);
                    check_valid(limit, "Address");
                    check_aligned(limit, "Address");
                    while ((unsigned long)EP != limit && ret == -259) {
                        ret = single_step();
                        if (no == c_TRACE) do_registers();
                        count[I]++;
                    }
                    if (ret != 0)
                        printf("HALT code %"PRId32" was returned at EP = $%X\n",
                               ret, EP);
                } else {
                    unsigned long limit = single_arg(arg, NULL), i;
                    for (i = 0; i < limit && ret == -259; i++) {
                        ret = single_step();
                        if (no == c_TRACE) do_registers();
                        count[I]++;
                    }
                    if (ret != 0)
                        printf("HALT code %"PRId32" was returned after %lu "
                               "steps\n", ret, i);
                }
            }
        }
        break;
    case c_SAVE:
        {
            const char *file = strtok(NULL, " ");
            long start, end;
            double_arg(strtok(NULL, ""), &start, &end, false);

            FILE *handle;
            if ((handle = fopen(globdirname(file), "wb")) == NULL)
                fatal("cannot open file %s", file);
            int ret = save_object(handle, start, (UCELL)((end - start) / CELL_W));
            fclose(handle);

            switch (ret) {
            case -1:
                fatal("save area contains an invalid address");
                break;
            case -3:
                fatal("error while saving module");
                break;
            default:
                break;
            }
        }
        break;
    case c_BLITERAL:
    case c_ILITERAL:
    case c_LITERAL:
        {
            int bytes;
            CELL value = (CELL)single_arg(strtok(NULL, ""), &bytes);

            switch (no) {
            case c_BLITERAL:
                if (bytes > 1)
                    fatal("the argument to BLITERAL must fit in a byte");
                ass((BYTE)value);
                break;
            case c_ILITERAL:
                if (ilit(value) == false)
                    fatal("ILITERAL %"PRId32" does not fit in the current instruction word", value);
                break;
            case c_LITERAL:
                lit(value);
                break;
            default: // This cannot happen
                break;
            }
        }
    default: // This cannot happen
        break;
    }

    switch (exception) {
    case -9:
        fatal("invalid address");
        break;
    case -23:
        fatal("address alignment exception");
        break;
    default:
    case 0:
        break;
    }
}


static void parse(char *input)
{
    // Handle shell command
    if (input[0] == '!') {
        int result = system(input + 1);
        if (result == -1)
            fatal("could not run command");
        else if (result != 0 && WIFEXITED(result))
            fatal("command exited with value %d", WEXITSTATUS(result));
        return;
    }

    // Hide any comment from the parser
    char *comment = strstr(input, "//");
    if (comment != NULL)
        *comment = '\0';

    char copy[MAXLEN];
    strcpy(copy, input);
    char *token = strtok(copy, strchr(copy, '=') == NULL ? " " : "=");
    if (token == NULL || strlen(token) == 0) return;
    upper(token);

    size_t i;
    for (i = strlen(token); input[i] == ' ' && i < strlen(input); i++)
        ;

    bool assign = false;
    if (i < strlen(input))
        assign = input[i] == '=';

    size_t no = search(token, command, commands);
    if (no != SIZE_MAX)
        do_command(no);
    else {
        if (assign)
            do_assign(token);
        else if (token[0] == 'O') {
            BYTE opcode = toass(token + 1);
            if (opcode != O_UNDEFINED)
                ass(opcode);
        } else {
            no = search(token, regist, registers);
            if (no == SIZE_MAX) {
                char *endp, *display;
                CELL adr = (CELL)parse_number(token, &endp);

                if (endp != &token[strlen(token)])
                    fatal("unknown command or register '%s'", token);

                check_valid(adr, "Address");
                if (!IS_ALIGNED(adr)) {
                    BYTE b;
                    load_byte(adr, &b);
                    display = xasprintf("$%"PRIX32": $%X (%d) (byte)", (UCELL)adr,
                                        b, b);
                } else {
                    CELL c;
                    load_cell(adr, &c);
                    display = xasprintf("$%"PRIX32": $%"PRIX32" (%"PRId32") (cell)", (UCELL)adr,
                                        (UCELL)c, c);
                }
                printf("%s\n", display);
                free(display);
            } else
                do_display(no, "%s\n");
        }
    }
}


static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void interactive_printf(const char *format, ...)
{
    if (interactive == false)
        return;

    va_list args;
    va_start(args, format);
    vprintf(format, args);
    va_end(args);
}

// Options table
struct option longopts[] = {
#define OPT(longname, shortname, arg, argstring, docstring) \
  {longname, arg, NULL, shortname},
#define ARG(argstring, docstring)
#define DOC(docstring)
#include "tbl_opts.h"
#undef OPT
#undef ARG
#undef DOC
  {0, 0, 0, 0}
};

#define VERSION_STRING PACKAGE_NAME" shell (C "PACKAGE_NAME" release "PACKAGE_VERSION")"
#define COPYRIGHT_STRING "(c) Reuben Thomas 1995-2018"

static void usage(void)
{
    char *shortopt, *buf;
    printf ("Usage: %s [OPTION...] [OBJECT-FILE ARGUMENT...]\n"
            "\n"
            "Run " PACKAGE_NAME ".\n"
            "\n",
            program_name);
#define OPT(longname, shortname, arg, argstring, docstring)               \
    shortopt = xasprintf(", -%c", shortname);                           \
    buf = xasprintf("--%s%s %s", longname, shortname ? shortopt : "", argstring); \
    printf("  %-26s%s\n", buf, docstring);
#define ARG(argstring, docstring)                 \
    printf("  %-26s%s\n", argstring, docstring);
#define DOC(text)                                 \
    printf(text "\n");
#include "tbl_opts.h"
#undef OPT
#undef ARG
#undef DOC
}

static CELL parse_memory_size(UCELL max)
{
    char *endptr;
    errno = 0;
    long size = (CELL)strtol(optarg, &endptr, 10);
    if (*optarg == '\0' || *endptr != '\0' || size <= 0 || (UCELL)size > max)
        die("memory size must be a positive number up to %"PRIu32, max);
    return size;
}

int main(int argc, char *argv[])
{
    char input[MAXLEN], *nl;

    set_program_name(argv[0]);
    interactive = isatty(fileno(stdin));

    // Options string starts with '+' to stop option processing at first non-option, then
    // leading ':' so as to return ':' for a missing arg, not '?'
    for (;;) {
        int this_optind = optind ? optind : 1, longindex = -1;
        int c = getopt_long(argc, argv, "+:dm:r:s:", longopts, &longindex);

        if (c == -1)
            break;
        else if (c == ':')
            die("option '%s' requires an argument", argv[this_optind]);
        else if (c == '?')
            die("unrecognised option '%s'\nTry '%s --help' for more information.", argv[this_optind], program_name);
        else if (c == 'd')
            longindex = 3;
        else if (c == 'm')
            longindex = 0;
        else if (c == 'r')
            longindex = 2;
        else if (c == 's')
            longindex = 1;

        switch (longindex) {
            case 0:
                memory_size = parse_memory_size((UCELL)MAX_MEMORY);
                break;
            case 1:
                HASHS = parse_memory_size((UCELL)MAX_STACK_SIZE);
                break;
            case 2:
                HASHR = parse_memory_size((UCELL)MAX_STACK_SIZE);
                break;
            case 3:
                debug_on_error = true;
                break;
            case 4:
                usage();
                exit(EXIT_SUCCESS);
            case 5:
                printf(PACKAGE_NAME " " VERSION "\n"
                       COPYRIGHT_STRING "\n"
                       PACKAGE_NAME " comes with ABSOLUTELY NO WARRANTY.\n"
                       "You may redistribute copies of " PACKAGE_NAME "\n"
                       "under the terms of the GNU General Public License.\n"
                       "For more information about these matters, see the file named COPYING.\n");
                exit(EXIT_SUCCESS);
            default:
                break;
            }
    }

    if ((memory = (CELL *)calloc(memory_size, CELL_W)) == NULL)
        die("could not allocate %"PRIu32" cells of memory", memory_size);
    reinit();

    argc -= optind;
    if (argc >= 1) {
        if (register_args(argc, argv + optind) != 0)
            die("could not map command-line arguments");
        FILE *handle = fopen(argv[optind], "rb");
        if (handle == NULL)
            die("cannot not open file %s", argv[optind]);
        int ret = load_object(handle, 0);
        fclose(handle);
        if (ret != 0)
            die("could not read file %s, or file is invalid", argv[optind]);

        int res = run();
        if (!debug_on_error || res >= 0)
            return res;
        warn("exception %d raised", res);
    } else
        interactive_printf("%s\n%s\n\n", VERSION_STRING, COPYRIGHT_STRING);

    while (1) {
        int jmp_val = setjmp(env);
        if (jmp_val == 0) {
            interactive_printf(">");
            if (fgets(input, MAXLEN, stdin) == NULL) {
                if (feof(stdin)) {
                    interactive_printf("\n"); // Empty line after prompt
                    exit(EXIT_SUCCESS);
                }
                die("input error");
            }
            lineno++;
            if ((nl = strrchr(input, '\n')))
                *nl = '\0';
            parse(input);
        } else if (interactive == false)
            exit(jmp_val);
    }
}