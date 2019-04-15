// Command-line options
//
// Copyright (c) 2009-2019 SMite authors
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

// DOC(text)
// OPT(long name, short name ('\0' for none), argument, argument docstring, docstring)
// ARG(argument, docstring)

OPT("core-dump", 'c', no_argument, "",
    "dump core on memory exception",
    core_dump = true;)

OPT("trace", '\0', required_argument, "FILE",
    "write dynamic instruction trace to FILE",
    {
        trace_fp = fopen(optarg, "wb");
        run_fn = trace_run;
        if (trace_fp == NULL)
            die("cannot not open file %s", optarg);
        warn("trace will be written to %s\n", optarg);
    })

OPT("help", '\0', no_argument, "",
    "display this help message and exit",
    usage();)

OPT("version", '\0', no_argument, "",
    "display version information and exit",
    {
        printf(PACKAGE_NAME " " VERSION " (%d-byte word, %s-endian)\n"
               "(c) SMite authors 1994-2019\n"
               PACKAGE_NAME " comes with ABSOLUTELY NO WARRANTY.\n"
               "You may redistribute copies of " PACKAGE_NAME "\n"
               "under the terms of the MIT/X11 License.\n",
               WORD_BYTES, ENDISM ? "big" : "little");
        exit(EXIT_SUCCESS);
    })

ARG("OBJECT-FILE", "load and run object OBJECT-FILE")
DOC("")
DOC("The ARGUMENTs are available to "PACKAGE_NAME".")
DOC("")
DOC("If an error occurs during execution, the exit status is the error code; if")
DOC("execution HALTs normally, the exit status is the top-most stack value.")
DOC("")
DOC("The memory and stack are automatically grown as required.")
DOC("")
DOC("Report bugs to "PACKAGE_BUGREPORT".")
