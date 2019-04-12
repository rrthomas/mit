// Front-end.
//
// (c) SMite authors 1995-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
#include <getopt.h>
#include <sys/stat.h>

#include "progname.h"
#include "xvasprintf.h"

#include "smite.h"


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

static smite_UWORD page_size;

static smite_UWORD round_up(smite_UWORD n, smite_UWORD multiple)
{
    return (n - 1) - (n - 1) % multiple + multiple;
}

static smite_state *S;

static void exit_function(void)
{
    smite_destroy(S);
}

FILE *trace_fp = NULL;
static int trace_run(smite_state *state)
{
    int ret = 0;
    do {
        fprintf(trace_fp, "%d\n", (int)(state->I & SMITE_INSTRUCTION_MASK));
        ret = smite_single_step(state);
    } while (ret == 0);
    return ret;
}

int main(int argc, char *argv[])
{
    set_program_name(argv[0]);
    // getpagesize() is obsolete, but gnulib provides it, and
    // sysconf(_SC_PAGESIZE) does not work on some platforms.
    page_size = getpagesize();

    bool core_dump = false;
    smite_UWORD memory_size = 0x100000U;
    smite_UWORD stack_size = 16384U;

    // Options string starts with '+' to stop option processing at first non-option, then
    // leading ':' so as to return ':' for a missing arg, not '?'
    for (;;) {
        int this_optind = optind ? optind : 1, longindex = -1;
        int c = getopt_long(argc, argv, "+:c", longopts, &longindex);

        if (c == -1)
            break;
        else if (c == ':')
            die("option '%s' requires an argument", argv[this_optind]);
        else if (c == '?')
            die("unrecognised option '%s'\nTry '%s --help' for more information.", argv[this_optind], program_name);
        else if (c == 'c')
            longindex = 0;

        switch (longindex) {
        case 0:
            core_dump = true;
            break;
        case 1:
            trace_fp = fopen(optarg, "wb");
            if (trace_fp == NULL)
                die("cannot not open file %s", optarg);
            warn("trace will be written to %s\n", optarg);
            break;
        case 2:
            usage();
            break;
        case 3:
            printf(PACKAGE_NAME " " VERSION " (%d-byte word, %s-endian)\n"
                   "(c) SMite authors 1994-2019\n"
                   PACKAGE_NAME " comes with ABSOLUTELY NO WARRANTY.\n"
                   "You may redistribute copies of " PACKAGE_NAME "\n"
                   "under the terms of the MIT/X11 License.\n",
                   WORD_BYTES, ENDISM ? "big" : "little");
            exit(EXIT_SUCCESS);
        default:
            break;
        }
    }

    argc -= optind;
    if (argc < 1)
        usage();

    S = smite_init(memory_size, stack_size);
    if (S == NULL)
        die("could not allocate virtual machine state");
    if (atexit(exit_function) != 0)
        die("could not register atexit handler");

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
            err = "file system error";
            break;
        case -2:
            err = "module invalid";
            break;
        case -3:
            err = "module has wrong ENDISM or WORD_BYTES";
            break;
        case -4:
            err = "address out of range or unaligned, or module too large";
            break;
        default:
            err = "unknown error!";
            break;
        }
    if (err != NULL)
        die("%s: %s", argv[optind], err);

    // Run code
    int (*run_fn)(smite_state *) = trace_fp ? trace_run : smite_run;
    for (;;) {
        int res;
        switch (res = run_fn(S)) {
        case 2:
            // Grow stack on demand
            if (S->BAD < S->stack_size ||
                S->BAD >= smite_uword_max - S->stack_size ||
                (res = smite_realloc_stack(S, round_up(S->stack_size + S->BAD, page_size))) != 0)
                return res;
            break;
        case 5:
        case 6:
            // Grow memory on demand
            if (S->BAD < S->memory_size ||
                (res = smite_realloc_memory(S, round_up(S->BAD, page_size))) != 0)
                return res;
            break;
        default:
            // Core dump on error
            if (core_dump) {
                warn("error %d raised at PC=%"PRI_XWORD"; BAD=%"PRI_XWORD,
                     res, S->PC, S->BAD);

                char *file = xasprintf("smite-core.%lu", (unsigned long)getpid());
                // Ignore errors; best effort only, in the middle of an error exit
                if ((fd = creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH)) >= 0) {
                    (void)smite_save_object(S, 0, S->memory_size, fd);
                    close(fd);
                    warn("core dumped to %s", file);
                } else
                    perror("open error");
                free(file);
            }
            return res == 128 ? 0 : res;
        }
    }
}
