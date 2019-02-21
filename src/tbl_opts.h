// Table of command-line options
//
// Copyright (c) 2009-2018 Reuben Thomas
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

// D: documentation line
// O: Option
// A: Action
//
// D(text)
// O(long name, short name ('\0' for none), argument, argument docstring, docstring)
// A(argument, docstring)

#define MEMORY_MESSAGE(type, max, def)                                  \
  "set " type " size to the given NUMBER of words\n"                    \
  "                            0 < NUMBER <= %"PRI_XWORD" [default %"PRI_XWORD"]", max, def
OPT("memory", 'm', required_argument, "NUMBER", MEMORY_MESSAGE("memory", smite_uword_max, smite_default_memory_size))
OPT("stack", 's', required_argument, "NUMBER", MEMORY_MESSAGE("stack", smite_uword_max, smite_default_stack_size))
OPT("core-dump", 'c', no_argument, "", "dump core on memory exception")
OPT("trace", '\0', required_argument, "FILE", "write dynamic instruction trace to FILE")
OPT("help", '\0', no_argument, "", "display this help message and exit")
OPT("version", '\0', no_argument, "", "display version information and exit")
ARG("OBJECT-FILE", "load and run object OBJECT-FILE")
DOC("")
DOC("The ARGUMENTs are available to "PACKAGE_NAME".")
DOC("")
DOC("Report bugs to "PACKAGE_BUGREPORT".")
