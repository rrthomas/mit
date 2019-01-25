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

#include <stdlib.h>
#include <stdbool.h>
#include <stdarg.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <getopt.h>
#include <sys/stat.h>

#include "progname.h"
#include "xvasprintf.h"

#include "smite.h"
#include "aux.h"


static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 0) void verror(const char *format, va_list args)
{
    fprintf(stderr, PACKAGE ": ");
    vfprintf(stderr, format, args);
    fprintf(stderr, "\n");
}

static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void warn(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
}

static _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void die(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
    exit(1);
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

static smite_WORD parse_memory_size(smite_UWORD max)
{
    char *endptr;
    errno = 0;
    long size = (smite_WORD)strtol(optarg, &endptr, 10);
    if (*optarg == '\0' || *endptr != '\0' || size <= 0 || (smite_UWORD)size > max)
        die("memory size must be a positive number up to %"PRI_UWORD, max);
    return size;
}

static void usage(void)
{
    char *doc, *shortopt, *buf;
    printf ("Usage: %s [OPTION...] [OBJECT-FILE ARGUMENT...]\n"
            "\n"
            "Run " PACKAGE_NAME ".\n"
            "\n",
            program_name);
#define OPT(longname, shortname, arg, argstring, docstring)             \
    doc = xasprintf(docstring);                                         \
    shortopt = xasprintf(", -%c", shortname);                           \
    buf = xasprintf("--%s%s %s", longname, shortname ? shortopt : "", argstring); \
    printf("  %-26s%s\n", buf, doc);                                    \
    free(doc);                                                          \
    free(shortopt);                                                     \
    free(buf);
#define ARG(argstring, docstring)                       \
    printf("  %-26s%s\n", argstring, docstring);
#define DOC(text)                               \
    printf(text "\n");
#include "tbl_opts.h"
#undef OPT
#undef ARG
#undef DOC
    exit(EXIT_SUCCESS);
}

int main(int argc, char *argv[])
{
    set_program_name(argv[0]);

    bool core_dump = false;
    smite_UWORD memory_size = smite_default_memory_size;
    smite_UWORD stack_size = smite_default_stack_size;
    smite_UWORD return_stack_size = smite_default_stack_size;

    // Options string starts with '+' to stop option processing at first non-option, then
    // leading ':' so as to return ':' for a missing arg, not '?'
    for (;;) {
        int this_optind = optind ? optind : 1, longindex = -1;
        int c = getopt_long(argc, argv, "+:cm:r:s:", longopts, &longindex);

        if (c == -1)
            break;
        else if (c == ':')
            die("option '%s' requires an argument", argv[this_optind]);
        else if (c == '?')
            die("unrecognised option '%s'\nTry '%s --help' for more information.", argv[this_optind], program_name);
        else if (c == 'c')
            longindex = 3;
        else if (c == 'm')
            longindex = 0;
        else if (c == 'r')
            longindex = 2;
        else if (c == 's')
            longindex = 1;

        switch (longindex) {
        case 0:
            memory_size = parse_memory_size(smite_max_memory_size);
            break;
        case 1:
            stack_size = parse_memory_size(smite_max_stack_size);
            break;
        case 2:
            return_stack_size = parse_memory_size(smite_max_stack_size);
            break;
        case 3:
            core_dump = true;
            break;
        case 4:
            usage();
            break;
        case 5:
            printf(PACKAGE_NAME " " VERSION "\n"
                   "(c) Reuben Thomas 1994-2019\n"
                   PACKAGE_NAME " comes with ABSOLUTELY NO WARRANTY.\n"
                   "You may redistribute copies of " PACKAGE_NAME "\n"
                   "under the terms of the GNU General Public License.\n"
                   "For more information about these matters, see the file named COPYING.\n");
            exit(EXIT_SUCCESS);
        default:
            break;
        }
    }

    argc -= optind;
    if (argc < 1)
        usage();

    smite_state *S = smite_init(memory_size, stack_size, return_stack_size);
    if (S == NULL)
        die("could not allocate virtual machine smite_state");

    if (smite_register_args(S, argc, argv + optind) != 0)
        die("could not map command-line arguments");

    // Load object file and report any error
    int fd = open(argv[optind], O_RDONLY);
    if (fd < 0)
        die("cannot not open file %s", argv[optind]);
    int ret = smite_load_object(S, 0, fd);
    close(fd);
    const char *err = NULL;
    if (ret < 0)
        switch (ret) {
        case -1:
            err = "address out of range or unaligned, or module too large";
            break;
        case -2:
            err = "module header invalid";
            break;
        case -3:
            err = "error while loading module";
            break;
        case -4:
            err = "module has wrong ENDISM";
            break;
        case -5:
            err = "module has wrong WORD_SIZE";
            break;
        default:
            err = "unknown error!";
            break;
        }
    if (err != NULL)
        die("%s: %s", argv[optind], err);

    // Run code
    int res = smite_run(S);

    // Core dump on error
    if (core_dump && (res == -23 || res == -9 || (res <= -256 && res >= -260))) {
        warn("exception %d raised at PC=%"PRI_XWORD, res, S->PC);

        char *file = xasprintf("smite-core.%lu", (unsigned long)getpid());
        // Ignore errors; best effort only, in the middle of an error exit
        if ((fd = creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH)) >= 0) {
            (void)smite_save_object(S, 0, S->MEMORY, fd);
            close(fd);
            warn("core dumped to %s", file);
        } else
            perror("open error");
        free(file);
    }

    smite_destroy(S);

    return res;
}
