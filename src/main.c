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

#include <assert.h>
#include <stdlib.h>
#include <stdarg.h>
#include <inttypes.h>
#include <errno.h>
#include <ctype.h>
#include <string.h>
#include <setjmp.h>
#include <unistd.h>
#include <fcntl.h>
#include <getopt.h>
#include <sys/wait.h>
#include <libgen.h>
#include <glob.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <regex.h>

#include "progname.h"
#include "xalloc.h"
#include "xvasprintf.h"

#include "public.h"
#include "aux.h"
#include "debug.h"
#include "opcodes.h"


static state *S;
static UWORD memory_size = DEFAULT_MEMORY; // Size of VM memory in words
UWORD stack_size = DEFAULT_STACK_SIZE;
UWORD return_stack_size = DEFAULT_STACK_SIZE;

static bool interactive;
static unsigned long lineno;
static jmp_buf env;

static bool core_dump = false;
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
#define R(reg, type, utype) #reg,
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "tbl_registers.h"
#undef R
#undef R_RO
};
enum registers {
#define R(reg, type, utype) r_##reg,
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "tbl_registers.h"
#undef R
#undef R_RO
};
static int registers = sizeof(regist) / sizeof(*regist);


static int creat1(const char *file)
{
    return creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
}

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

static void check_valid(UWORD adr, const char *quantity)
{
    if (native_address(S, adr, false) == NULL)
        fatal("%s is invalid", quantity);
}

static void check_range(UWORD start, UWORD end, const char *quantity)
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

static WORD parse_instruction(const char *token)
{
    WORD opcode = O_UNDEFINED;
    if (token[0] == 'O') {
        opcode = toass(token + 1);
        if (opcode == O_UNDEFINED)
            fatal("invalid opcode");
    }
    return opcode;
}

static long long parse_number(const char *s, char **endp)
{
    return (s[0] == '0' && (s[1] == 'X' || s[1] == 'x')) ? strtoll(s + 2, endp, 16) :
        strtoll(s, endp, 10);
}

static long long single_arg(const char *s, int *bytes)
{
    if (s == NULL)
        fatal("too few arguments");

    char *endp;
    long long n = parse_number(s, &endp);

    if (endp != &s[strlen(s)])
        fatal("invalid number");

    if (bytes != NULL)
        *bytes = byte_size(n);

    return n;
}

static void double_arg(char *arg1, bool plus, char *arg2, long long *start, long long *end)
{
    bool add = true;

    if (arg1 != NULL)
        *start = single_arg(arg1, NULL);
    if (arg2 != NULL) {
        *end = single_arg(arg2, NULL);
        add = plus;
    }

    if (add)
        *end += *start;
}


static void disassemble(UWORD start, UWORD end)
{
    for (UWORD p = start; p < end; ) {
        printf("%#08"PRI_XWORD": ", p);

        WORD val;
        int type = decode_instruction(S, &p, &val);
        if (type < 0)
            printf("Error reading memory");
        else {
            const char *s = disass(type, val);
            if (strcmp(s, "undefined") == 0)
                printf("Undefined instruction");
            else
                printf("%s", s);
        }
        putchar('\n');
    }
}


static void reinit(void)
{
    destroy(S);
    S = init(memory_size, stack_size, return_stack_size);
    if (S == NULL)
        die("could not allocate virtual machine state");

    start_ass(S, S->PC);
}


static int save_object(int fd, UWORD address, UWORD length)
{
    uint8_t *ptr = native_address_range_in_one_area(S, address, length, false);
    if (!IS_ALIGNED(address) || ptr == NULL)
        return -1;

    if (write(fd, PACKAGE_UPPER, sizeof(PACKAGE_UPPER)) != sizeof(PACKAGE_UPPER))
        return -2;

    ssize_t bytes_left = MAGIC_LENGTH - strlen(PACKAGE_UPPER) - 1;

    BYTE buf[INSTRUCTION_MAX_CHUNKS] = {};

    if (write(fd, &buf[0], bytes_left) != bytes_left)
        return -2;

    ssize_t len = encode_instruction_native(&buf[0], INSTRUCTION_NUMBER, S->ENDISM);
    if (write(fd, &buf[0], len) != len)
        return -2;

    len = encode_instruction_native(&buf[0], INSTRUCTION_NUMBER, WORD_SIZE);
    if (write(fd, &buf[0], len) != len)
        return -2;

    len = encode_instruction_native(&buf[0], INSTRUCTION_NUMBER, length);
    if (write(fd, &buf[0], len) != len)
        return -2;

    if (write(fd, ptr, length) != length)
        return -2;

    return 0;
}


static void do_assign(char *token, char *number)
{
    long long value;
    int bytes = 4;

    upper(number);
    value = parse_instruction(number);
    if (value != O_UNDEFINED)
        bytes = 1;
    else
        value = single_arg(number, &bytes);

    int no = search(token, regist, registers);
    switch (no) {
#define R(reg, type, utype)                     \
        case r_##reg:                           \
            S->reg = (type)value;               \
            break;
#define R_RO(reg, type, utype)                          \
        case r_##reg:                                   \
            fatal("cannot assign to %s", regist[no]);   \
            break;
#include "tbl_registers.h"
#undef R
#undef R_RO
        default:
            {
                WORD adr = (WORD)single_arg(token, NULL);

                check_valid(adr, "Address");
                if (!IS_ALIGNED(adr) && bytes > 1)
                    fatal("only a byte can be assigned to an unaligned address");
                if (bytes == 1)
                    store_byte(S, adr, value);
                else
                    store_word(S, adr, value);
            }
    }
    if (no == r_PC)
        start_ass(S, S->PC);
}

static void do_display(size_t no, const char *format)
{
    char *display;

    switch (no) {
#define R(reg, type, utype)                                         \
    case r_##reg:                                                   \
        display = xasprintf(#reg" = %"PRI_X##type" (%"PRI_##type")", (utype)S->reg, S->reg); \
        break;
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "tbl_registers.h"
#undef R
    default:
        display = xasprintf("unknown register");
        break;
    }
    switch (no) {
    case r_I:
        {
            char *new_display = xasprintf("%s (%-10s)", display, disass(S->ITYPE, S->I));
            free(display);
            display = new_display;
        }
        break;
    case r_ITYPE:
        break;
    default:
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
    do_display(r_PC, "%-25s");
    do_display(r_I, "%-22s");
    putchar('\n');
}

static void do_command(int no, char *arg1, bool plus1, char *arg2, bool plus2, char *arg3)
{
    int exception = 0;

    switch (no) {
    case c_TOD:
        {
            long long value = single_arg(arg1, NULL);
            PUSH(value);
        }
        break;
    case c_TOR:
        {
            long long value = single_arg(arg1, NULL);
            PUSH_STACK(S->RP, S->R0, S->RSIZE, value);
        }
        break;
    case c_DISASSEMBLE:
        {
            long long start = (S->PC <= 16 ? 0 : S->PC - 16), end = 64;
            double_arg(arg1, plus1, arg2, &start, &end);
            check_range(start, end, "Address");
            disassemble((UWORD)start, (UWORD)end);
        }
        break;
    case c_DFROM:
        {
            WORD value = POP;
            printf("%"PRI_WORD" (%#"PRI_XWORD")\n", value, (UWORD)value);
        }
        break;
    case c_DATA:
    case c_STACKS:
        show_data_stack(S);
        if (no == c_STACKS)
            goto c_ret;
        break;
    case c_DUMP:
        {
            long long start = (S->PC <= 64 ? 0 : S->PC - 64), end = 256;
            double_arg(arg1, plus1, arg2, &start, &end);
            check_range(start, end, "Address");
            while (start < end) {
                printf("%#08lx ", (unsigned long)start);
                const int chunk = 16;
                char ascii[chunk];
                for (int i = 0; i < chunk && start < end; i++) {
                    BYTE byte;
                    load_byte(S, start + i, &byte);
                    if (i % 8 == 0)
                        putchar(' ');
                    printf("%02x ", byte);
                    ascii[i] = isprint(byte) ? byte : '.';
                }
                start += chunk;
                printf(" |%.*s|\n", chunk, ascii);
            }
        }
        break;
    case c_INITIALISE:
        reinit();
        break;
    case c_LOAD:
        {
            reinit();

            UWORD adr = 0;
            if (arg2 != NULL)
                adr = single_arg(arg2, NULL);

            int fd = open(globfile(arg1), O_RDONLY);
            if (fd < 0)
                fatal("cannot open file %s", arg1);
            int ret = load_object(S, fd, adr);
            close(fd);

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
            case -4:
                fatal("module has wrong WORD_SIZE");
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
            WORD value = POP_STACK(S->RP, S->R0, S->RSIZE);
            printf("%#"PRI_XWORD" (%"PRI_WORD")\n", (UWORD)value, value);
        }
        break;
    c_ret:
    case c_RETURN:
        show_return_stack(S);
        break;
    case c_RUN:
        printf("HALT code %"PRI_WORD" was returned\n", run(S));
        break;
    case c_STEP:
    case c_TRACE:
        {
            WORD ret = -258;

            if (arg1 == NULL) {
                if ((ret = single_step(S)))
                    printf("HALT code %"PRI_WORD" was returned\n", ret);
                if (no == c_TRACE) do_registers();
            } else {
                upper(arg1);
                if (strcmp(arg1, "TO") == 0) {
                    unsigned long long limit = single_arg(arg2, NULL);
                    check_valid(limit, "Address");
                    while ((unsigned long)S->PC != limit && ret == -258) {
                        ret = single_step(S);
                        if (no == c_TRACE) do_registers();
                    }
                    if (ret != 0)
                        printf("HALT code %"PRI_WORD" was returned at PC = %#"PRI_XWORD"\n",
                               ret, S->PC);
                } else {
                    unsigned long long limit = single_arg(arg1, NULL), i;
                    for (i = 0; i < limit && ret == -258; i++) {
                        ret = single_step(S);
                        if (no == c_TRACE) do_registers();
                    }
                    if (ret != 0)
                        printf("HALT code %"PRI_WORD" was returned after %llu "
                               "steps\n", ret, i);
                }
            }
        }
        break;
    case c_SAVE:
        {
            long long start = 0, end = ass_current(S);
            double_arg(arg2, plus2, arg3, &start, &end);

            int fd;
            if ((fd = creat1(globdirname(arg1))) < 0)
                fatal("cannot open file %s", arg1);
            int ret = save_object(fd, start, (UWORD)((end - start)));
            close(fd);

            switch (ret) {
            case -1:
                fatal("save area contains an invalid address");
                break;
            case -2:
                fatal("error while saving module");
                break;
            default:
                break;
            }
        }
        break;
    case c_BYTE:
    case c_NUMBER:
    case c_POINTER:
        {
            int bytes;
            long long value = single_arg(arg1, &bytes);

            switch (no) {
            case c_BYTE:
                if (bytes > 1)
                    fatal("the argument to BYTE must fit in a byte");
                ass_byte(S, (BYTE)value);
                break;
            case c_NUMBER:
                if (bytes > WORD_SIZE)
                    fatal("the argument to NUMBER must fit in a word");
                ass_number(S, value);
                break;
            case c_POINTER:
                ass_native_pointer(S, (void *)value);
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


static char *pmatch_token(char *input, regmatch_t pmatch)
{
    char *token = NULL;
    if (pmatch.rm_so != -1)
        token = strndup(input + pmatch.rm_so, pmatch.rm_eo - pmatch.rm_so);
    return token;
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

    // Parse the rest of the line
    regex_t preg;
    assert(regcomp(&preg, "^[[:space:]]*([-[:alnum:]_]+)?[[:space:]]*(=)?[[:space:]]*([-[:alnum:]/._~-]+)?[[:space:]]*(\\+)?[[:space:]]*([[:alnum:]/._~-]+)?[[:space:]]*(\\+)?[[:space:]]*([[:alnum:]/._~-]+)?$", REG_EXTENDED) == 0);
#define MATCHES 7
    // Arguments are at position 1, 3, 5, 7
    // Equals sign is at 2, plus signs at 4, 6
    regmatch_t pmatch[MATCHES + 1];
    int res = regexec(&preg, input, MATCHES + 1, &pmatch[0], 0);
    regfree(&preg);
    if (res == REG_NOMATCH)
        fatal("syntax error");

    static char *token = NULL;
    free(token);
    token = pmatch_token(input, pmatch[1]);
    bool assign = pmatch[2].rm_so != -1;
    static char *sym2 = NULL;
    free(sym2);
    sym2 = pmatch_token(input, pmatch[3]);
    bool plus1 = pmatch[4].rm_so != -1;
    static char *sym3 = NULL;
    free(sym3);
    sym3 = pmatch_token(input, pmatch[5]);
    bool plus2 = pmatch[6].rm_so != -1;
    static char *sym4 = NULL;
    free(sym4);
    sym4 = pmatch_token(input, pmatch[7]);

    // If we have only whitespace silently exit
    if (token == NULL && !assign && sym2 == NULL && !plus1)
        return;

    if (token == NULL)
        fatal("syntax error");
    upper(token);
    size_t no = search(token, command, commands);
    if (no != SIZE_MAX)
        do_command(no, sym2, plus1, sym3, plus2, sym4);
    else {
        if (assign) {
            if (plus1 || sym3 != NULL)
                fatal("syntax error");
            do_assign(token, sym2);
        } else {
            WORD opcode = parse_instruction(token);
            if (opcode != O_UNDEFINED) {
                ass_action(S, opcode);
                return;
            }

            no = search(token, regist, registers);
            if (no == SIZE_MAX) {
                char *endp, *display;
                UWORD adr = (UWORD)parse_number(token, &endp);

                if (endp != &token[strlen(token)])
                    fatal("unknown command or register '%s'", token);

                check_valid(adr, "Address");
                if (!IS_ALIGNED(adr)) {
                    BYTE b;
                    load_byte(S, adr, &b);
                    display = xasprintf("%#"PRI_XWORD": %#x (%d) (byte)", (UWORD)adr, b, b);
                } else {
                    WORD c;
                    load_word(S, adr, &c);
                    display = xasprintf("%#"PRI_XWORD": %#"PRI_XWORD" (%"PRI_WORD") (word)", (UWORD)adr,
                                        (UWORD)c, c);
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
    char *doc, *shortopt, *buf;
    printf ("Usage: %s [OPTION...] [OBJECT-FILE ARGUMENT...]\n"
            "\n"
            "Run " PACKAGE_NAME ".\n"
            "\n",
            program_name);
#define OPT(longname, shortname, arg, argstring, ...)                   \
    doc = xasprintf(__VA_ARGS__);                                       \
    shortopt = xasprintf(", -%c", shortname);                           \
    buf = xasprintf("--%s%s %s", longname, shortname ? shortopt : "", argstring); \
    printf("  %-26s%s\n", buf, doc);
#define ARG(argstring, docstring)                 \
    printf("  %-26s%s\n", argstring, docstring);
#define DOC(text)                                 \
    printf(text "\n");
#include "tbl_opts.h"
#undef OPT
#undef ARG
#undef DOC
}

static WORD parse_memory_size(UWORD max)
{
    char *endptr;
    errno = 0;
    long size = (WORD)strtol(optarg, &endptr, 10);
    if (*optarg == '\0' || *endptr != '\0' || size <= 0 || (UWORD)size > max)
        die("memory size must be a positive number up to %"PRI_UWORD, max);
    return size;
}

static void dump_core(int exception)
{
    warn("exception %d raised at PC=%#"PRI_XWORD, exception, S->PC);

    char *file = xasprintf("smite-core.%lu", (unsigned long)getpid());
    int fd;
    // Ignore errors; best effort only, in the middle of an error exit
    if ((fd = creat1(file)) >= 0) {
        (void)save_object(fd, 0, S->MEMORY);
        close(fd);
        warn("core dumped to %s", file);
    } else
        perror("open error");
    free(file);
}

int main(int argc, char *argv[])
{
    set_program_name(argv[0]);
    interactive = isatty(fileno(stdin));

    // Options string starts with '+' to stop option processing at first non-option, then
    // leading ':' so as to return ':' for a missing arg, not '?'
    for (;;) {
        int this_optind = optind ? optind : 1, longindex = -1;
        int c = getopt_long(argc, argv, "+:cdm:r:s:", longopts, &longindex);

        if (c == -1)
            break;
        else if (c == ':')
            die("option '%s' requires an argument", argv[this_optind]);
        else if (c == '?')
            die("unrecognised option '%s'\nTry '%s --help' for more information.", argv[this_optind], program_name);
        else if (c == 'c')
            longindex = 3;
        else if (c == 'd')
            longindex = 4;
        else if (c == 'm')
            longindex = 0;
        else if (c == 'r')
            longindex = 2;
        else if (c == 's')
            longindex = 1;

        switch (longindex) {
        case 0:
            memory_size = parse_memory_size((UWORD)MAX_MEMORY);
            break;
        case 1:
            stack_size = parse_memory_size((UWORD)MAX_STACK_SIZE);
            break;
        case 2:
            return_stack_size = parse_memory_size((UWORD)MAX_STACK_SIZE);
            break;
        case 3:
            core_dump = true;
            break;
        case 4:
            debug_on_error = true;
            break;
        case 5:
            usage();
            exit(EXIT_SUCCESS);
        case 6:
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

    reinit();

    argc -= optind;
    if (argc >= 1) {
        if (register_args(S, argc, argv + optind) != 0)
            die("could not map command-line arguments");
        int fd = open(argv[optind], O_RDONLY);
        if (fd < 0)
            die("cannot not open file %s", argv[optind]);
        int ret = load_object(S, fd, 0);
        close(fd);
        if (ret != 0)
            die("could not read file %s, or file is invalid", argv[optind]);

        int res = run(S);
        if (core_dump && (res == -23 || res == -9 || (res <= -256 && res >= -260)))
            dump_core(res);
        if (!debug_on_error || res >= 0)
            return res;
        warn("exception %d raised", res);
    } else
        interactive_printf("%s\n%s\n\n", VERSION_STRING, COPYRIGHT_STRING);

    while (1) {
        int jmp_val = setjmp(env);
        if (jmp_val == 0) {
            static char *input = NULL;
            static size_t len = 0;
            interactive_printf(">");
            if (getline(&input, &len, stdin) == -1) {
                if (feof(stdin)) {
                    interactive_printf("\n"); // Empty line after prompt
                    exit(EXIT_SUCCESS);
                }
                die("input error");
            }
            lineno++;
            char *nl;
            if ((nl = strrchr(input, '\n')))
                *nl = '\0';
            parse(input);
        } else if (interactive == false)
            exit(jmp_val);
    }
}
